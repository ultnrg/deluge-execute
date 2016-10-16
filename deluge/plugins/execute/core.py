# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrew Resch <andrewresch@gmail.com>
#
# This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
# the additional special exception to link portions of this program with the OpenSSL library.
# See LICENSE for more details.
#

import hashlib
import logging
import os
import time
import urllib2

from twisted.internet.utils import getProcessOutputAndValue

import deluge.component as component
from deluge.common import utf8_encoded, windows_check
from deluge.configmanager import ConfigManager
from deluge.core.rpcserver import export
from deluge.event import DelugeEvent
from deluge.plugins.pluginbase import CorePluginBase

log = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "commands": []
}

EXECUTE_ID = 0
EXECUTE_EVENT = 1
EXECUTE_COMMAND = 2
EXECUTE_TYPE = 3
EXECUTE_LABEL = 4
EXECUTE_DELAY = 5

EVENT_MAP = {
    "complete": "TorrentFinishedEvent",
    "added": "TorrentAddedEvent",
    "removed": "TorrentRemovedEvent",
    "copied":"TorrentCopiedEvent"
}


class ExecuteCommandAddedEvent(DelugeEvent):
    """
    Emitted when a new command is added.
    """
    def __init__(self, command_id, event, command, type, torrentlabel, delay):
        self._args = [command_id, event, command, type, torrentlabel, delay]


class ExecuteCommandRemovedEvent(DelugeEvent):
    """
    Emitted when a command is removed.
    """
    def __init__(self, command_id):
        self._args = [command_id]


class Core(CorePluginBase):
    def enable(self):
        self.config = ConfigManager("execute.conf", DEFAULT_CONFIG)
        event_manager = component.get("EventManager")
        self.registered_events = {}
        self.preremoved_cache = {}
		
        # Go through the commands list and register event handlers
        for command in self.config["commands"]:
            event = command[EXECUTE_EVENT]
            if event in self.registered_events:
                continue
            def create_event_handler(event):
                def event_handler(torrent_id, *arg):
                    #log.debug("Bleh %s", *arg)
                    #log.debug("Bleh %s", arg)
                    self.execute_commands(torrent_id, event, *arg)
                return event_handler
            event_handler = create_event_handler(event)
            event_manager.register_event_handler(EVENT_MAP[event], event_handler)
            if event == "removed":
                event_manager.register_event_handler("PreTorrentRemovedEvent", self.on_preremoved)
            self.registered_events[event] = event_handler

        log.debug("Execute core plugin enabled!")

    def on_preremoved(self, torrent_id):
        # Get and store the torrent info before it is removed
        torrent = component.get("TorrentManager").torrents[torrent_id]
        info = torrent.get_status(["name", "download_location"])
        self.preremoved_cache[torrent_id] = [utf8_encoded(torrent_id), utf8_encoded(info["name"]),
                                             utf8_encoded(info["download_location"])]

    def execute_commands(self, torrent_id, event, *arg):
        log.debug("EXECUTE: did we start execute_commands? Event is %s", event)
        torrent = component.get("TorrentManager").torrents[torrent_id]
        if event == "added":# and arg[0]:
            log.debug("EXECUTE: can't get from state, ending")
            # No futher action as from_state (arg[0]) is True
            return
        elif event == "removed":
            torrent_id, torrent_name, download_location = self.preremoved_cache.pop(torrent_id)
        else:
            log.debug("EXECUTE: Status: %s", torrent.get_status({}))
            info = torrent.get_status([ "name", "save_path", "move_on_completed", "move_on_completed_path"])
            log.debug("EXECUTE: Info: %s", info)
            # Grab the torrent name and download location
            # getProcessOutputAndValue requires args to be str
            torrent_id = utf8_encoded(torrent_id)
            log.debug("EXECUTE: TorrentID: %s", torrent_id)
            torrent_name = utf8_encoded(info["name"])
            log.debug("EXECUTE: Torrent name: %s", torrent_name)
            download_location = utf8_encoded(info["move_on_completed_path"]) if info["move_on_completed"] else utf8_encoded(info["save_path"])
            # Grab the torrent label
            log.debug("EXECUTE: download_location: %s", download_location)

        get_label = component.get("Core").get_torrent_status(torrent_id,["label"])
        label = utf8_encoded(get_label["label"])
        log.debug("EXECUTE: Label: %s", label)

        log.debug("EXECUTE:Running commands for %s", event)

        def log_error(result, command):
            (stdout, stderr, exit_code) = result
            if exit_code:
                log.warn("Command '%s' failed with exit code %d", command, exit_code)
                if stdout:
                    log.warn("stdout: %s", stdout)
                if stderr:
                    log.warn("stderr: %s", stderr)
        
        log.debug("EXECUTE: Start of new code")
        #get label from torrent
        get_label = component.get("Core").get_torrent_status(torrent_id,["label"])
        label = get_label["label"]

        # Go through and execute all the commands
        log.debug("EXECUTE: Starting the loop of commands. Label marked as: %s", label)
        for command in self.config["commands"]:
            log.debug("EXECUTE: Command is as follows: %s", command)
            if command[EXECUTE_EVENT] == event and command[EXECUTE_LABEL].upper() == label.upper():
                log.debug("EXECUTE: Label and event have been matched.")
                delay = command[EXECUTE_DELAY]
                if delay.isdigit():
                   log.debug("EXECUTE: Going to delay the script now by %s seconds.", delay)
                   time.sleep(float(delay))
                else:
                   log.debug("EXECUTE: Delay is not a number, so delay was not run. Current delay is: %s", delay)
				   
                # Mark args based on params
                cmd = command[EXECUTE_COMMAND]
                log.debug("EXECUTE: Raw Command: %s", cmd)
                cmd = cmd.replace("<id>",torrent_id)
                cmd = cmd.replace("<na>",torrent_name)
                cmd = cmd.replace("<dl>",download_location)
                cmd = cmd.replace("<lb>",label)
                cmd_args = ""
                if cmd.count('"') > 1: # if there are two quotations, we need to get everything inside the quotes as the cmd
                    cmd_groups = cmd.split('"')
                    cmd_groups = '"'.join(cmd_groups[:2]), '"'.join(cmd_groups[2:])
                    cmd = cmd_groups[0] + '"'
                    cmd_args = cmd_groups[1]
                    if len(cmd_args) > 0:
                        if cmd_args[0] == " ": # if the args start with a space, get rid of it
                            cmd_args = cmd_args[1:]
                else:
                    if " " in cmd:
                        cmd_args = cmd.split(" ", 1)[1]
                        cmd = cmd.split(" ", 1)[0]
                log.debug("EXECUTE: Command processed. Command: %s; Arguments: %s", cmd, cmd_args)
                if command[EXECUTE_TYPE] == "script":
                   log.debug("EXECUTE: This is a script")
                   cmd = os.path.expandvars(cmd)
                   cmd = os.path.expanduser(cmd)
                   
                   #cmd_args = [torrent_id, torrent_name, download_location]
                   if windows_check:
                       # Escape ampersand on windows (see #2784)
                       cmd_args = [cmd_args.replace("&", "^^^&") for cmd_arg in cmd_args]
                       cmd = [cmd.replace("&", "^^^&") for cmd_arg in cmd]
                   
                   if os.path.isfile(cmd) and os.access(cmd, os.X_OK):
                       log.debug("EXECUTE: Running command with args: %s %s", cmd, cmd_args)
                       d = getProcessOutputAndValue(cmd, cmd_args, env=os.environ)
                       d.addCallback(log_error, cmd)
                   else:
                       log.error("EXECUTE: Execute script not found or not executable")
                if command[EXECUTE_TYPE] == "url":
                    url = cmd
                    log.debug("EXECUTE: Calling the following URL: %s", url)
                    req = urllib2.Request(url)
                    response = urllib2.urlopen(req)
                    the_page = response.read()
                    log.debug("EXECUTE: URL response page: %s", the_page)

    def disable(self):
        self.config.save()
        event_manager = component.get("EventManager")
        for event, handler in self.registered_events.iteritems():
            event_manager.deregister_event_handler(event, handler)
        log.debug("Execute core plugin disabled!")

    # Exported RPC methods #
    @export
    def add_command(self, event, command, type, torrentlabel, delay):
        command_id = hashlib.sha1(str(time.time())).hexdigest()
        self.config["commands"].append((command_id, event, command, type, torrentlabel, delay))
        self.config.save()
        component.get("EventManager").emit(ExecuteCommandAddedEvent(command_id, event, command, type, torrentlabel, delay))

    @export
    def get_commands(self):
        return self.config["commands"]

    @export
    def remove_command(self, command_id):
        for command in self.config["commands"]:
            if command[EXECUTE_ID] == command_id:
                self.config["commands"].remove(command)
                component.get("EventManager").emit(ExecuteCommandRemovedEvent(command_id))
                break
        self.config.save()

    @export
    def save_command(self, command_id, event, cmd):
        for i, command in enumerate(self.config["commands"]):
            if command[EXECUTE_ID] == command_id:
                type = command[EXECUTE_TYPE]
                label = command[EXECUTE_LABEL]
                delay = command[EXECUTE_DELAY]
                self.config["commands"][i] = (command_id, event, cmd, type, label, delay)
                break
        self.config.save()
