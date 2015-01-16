<?php

if (isset($_SESSION['STATUS'])) { 
	switch ($_SESSION['STATUS']) {
		case "FAIL":
			// something probably failed
			echo '<p class="error">Uh oh. No results found in directory. Something went wrong.</p>'; 
			break;
		case "SUCCESS": 
			foreach (scandir($_SESSION['FULLRESPATH']) as $file) {
				if ('.' === $file) continue;
				if ('..' === $file) continue;

				if (is_dir($_SESSION['FULLRESPATH'].$file)) {
					if (file_exists($_SESSION['FULLRESPATH'].$file."/index.php")) {	// if we find index.php in any subdirs
						// add this directory link to results
						echo "<a href=".$_SESSION['FULLRESPATH'].$file.'/index.php'." target=\"_blank\">/".$file."</a><br/>";
					}
				}
			}
			break;
	}
}

