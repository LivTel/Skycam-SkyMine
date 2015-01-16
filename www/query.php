<?php 

$LINE_LIMIT = 50;

ini_set('display_errors',1); 
error_reporting(E_ALL);

include 'session.php';
include 'config.php';

// exec pipeline if POST['process'] is true
function exec_pipeline($divName)
{
	global $LINE_LIMIT;

	// construct database clause
	$databaseClause = "";
        if (isset($_POST['senddbquery']) && ($_POST['senddbquery'] == "on"))
	{
        	if (isset($_POST['dbclobber']) && ($_POST['dbclobber'] == "overwrite"))
		{
			$databaseClause = "--sdb --odb";
		} else if (isset($_POST['dbclobber']) && ($_POST['dbclobber'] == "ignore"))
		{
			$databaseClause = "--sdb";
		}
	}

	// make a uniquely identifiable directory in results directory to store this run
        $id = uniqid();
        $_SESSION['FULLRESPATH'] = $_SESSION['RESROOTPATH'].$id."/";
        mkdir($_SESSION['FULLRESPATH']);

	// disable form submit
	print "
	<script type=\"text/javascript\">
		$(\"#formcontrols :input\").attr(\"disabled\", true);
	</script>
	";

	// execute parent pipe process (forks child processes for each date)
	$handle = popen($_SESSION['SRCPATH'].'run_pipe.py --root '.$_SESSION['ROOTPATH'].' --res '.$_SESSION['FULLRESPATH'].' --from "'.$_POST['datefrom'].'" --to "'.$_POST['dateto'].'" --pl --i '.$_POST['inst'].' '.$databaseClause.' 2>&1 | tee '.$_SESSION['FULLRESPATH'].'log', 'r');
	$console_content = array();
	while (!feof($handle)) {
		// get new content from console and add to array at start
                array_unshift($console_content, trim(addslashes(fgets($handle))));
		// truncate content to get last $LINE_LIMIT lines (otherwise console gets slow/hangs!)
		$console_content = array_slice($console_content, 0, $LINE_LIMIT);
		$this_content = implode("<br/>", array_reverse($console_content)); // requires array_reverse() to get in oldest-first order
		// append to div and move scrollbar to bottom
		print "
		<script type=\"text/javascript\">
			div = document.getElementById('".$divName."');
			div.innerHTML = '".$this_content."';
			div.scrollTop = div.scrollHeight;
		</script>
		";

		flush();
		ob_flush();
	}
	pclose($handle);

        // check result is valid (crude - just basically check for a single index.php in any subdir)
	$_SESSION['STATUS'] = 'FAIL'; 	// init as FAIL
	foreach (scandir($_SESSION['FULLRESPATH']) as $file) {
		if ('.' === $file) continue;
		if ('..' === $file) continue;

		if (is_dir($_SESSION['FULLRESPATH'].$file)) {
			if (file_exists($_SESSION['FULLRESPATH'].$file."/index.php")) {	// if we find index.php in any subdirs
				$_SESSION['STATUS'] = 'SUCCESS';			// reassign as SUCCESS
			}
		}
	}

	// renable form submit
	print "
	<script type=\"text/javascript\">
		$(\"#formcontrols :input\").attr(\"disabled\", false);
	</script>
	";
}
?>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<link rel="stylesheet" type="text/css" href="stylesheet.css">
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.2/jquery.min.js"></script>
<script type="text/javascript" src="js/jquery-simple-datetimepicker/jquery.simple-dtpicker.js"></script>
<link type="text/css" href="js/jquery-simple-datetimepicker/jquery.simple-dtpicker.css" rel="stylesheet"/>
<script type="text/javascript">
function isResultPaneVisible()
{
	if ($('#result_content').is(":hidden"))
		return false;
	else
		return true;
}

function toggleResultPane()
{
	if (isResultPaneVisible())
	{
		$('#results_toggle_pane').html("<a href=\"#\">expand</a>");
		$('#result_content').slideUp('slow');
	} else 
	{
		$('#results_toggle_pane').html("<a href=\"#\">collapse</a>");
		$('#result_content').slideDown('slow');
	}
}

</script>
</head>

<body>
<?php include("query_banner.php"); ?>
<div id="container" class="container">
	</p>
	<div id="controls" class="controls">
		<div class="bordertitle">Controls</div>
		<?php include("query_controls_content.php"); ?>	
	</div>
	<div id="console" class="console">
		<div class="bordertitle">Console</div>
		<div id="console_content" class="console_content"></div>
	</div>
	<div id="result" class="result">
		<div class="bordertitle">Results</div>
		<div id="results_toggle_pane" style="text-align: right; font-size: 10px;"><a href="#">expand</a></div>
		<br/>
		<div id="result_content" class="result_content">
			<br/>
			<?php if (isset($_POST['process']) && ($_POST['process'] == True))
			{
				$res = exec_pipeline("console_content");			// execute pipeline
				include("query_results_content.php");				// append results content to results div
				?>
				<!-- bring down results div -->
				<script type="text/javascript">
					if (!isResultPaneVisible())
						toggleResultPane();
				</script>
				<?php
			}
			?>
		</div>
		<script type="text/javascript">
		$("#results_toggle_pane").click(function(){
			toggleResultPane();
		});
		</script>
	</div>
</div>

</body>
</html>

