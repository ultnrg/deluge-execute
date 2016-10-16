deluge-execute
====================

This plugin for [Deluge][1] extends the original [execute][2] plugin.

####Added features:
-  Abilty to process URLs
-  Added timer to run script xx seconds after event fires
-  Added TorrentCopied event (CopyCompleted plugin)
-  Added support for labels - only execute if label matches
-  Added parameter support, removed hard coded arguments

	#####Parameters:
	
	-  &lt;id&gt; - torrent_id	
	-  &lt;na&gt; - torrent_name
	-  &lt;dl&gt; - download_location
	-  &lt;lb&gt; - label
	
####Notes:

If path has spaces in it, make sure you wrap the path in double quotations. E.g. "C:\Program Files\Path\To\Script.bat"

Params can be added anywhere, not just at the end.

####Example:

Label = movies

TorrentID = 123

"C:\My Downloads\\&lt;lb&gt;\script.bat" &lt;id&gt; <id> --> C:\My Downloads\movies\script.bat 123


  [1]: http://deluge-torrent.org
  [2]: http://dev.deluge-torrent.org/wiki/Plugins/Execute
  
  