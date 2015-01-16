<?php 

	// !!! DEFINE SKYMINE BASE PATH !!!
	$SKYMINE_PATH = "/skycam/SkyMine";

        // define useful paths relative to base
        $WWW_PATH = $SKYMINE_PATH."/www";
        $WWW_JS_PATH = $WWW_PATH."/js";

        $ETC_PATH = $SKYMINE_PATH."/etc";
        $ETC_PIPE_PATH = $ETC_PATH."/pipe";
	$ETC_PIPE_PARAMST_PATH = $ETC_PIPE_PATH."/params_T";
	$ETC_PIPE_PARAMSZ_PATH = $ETC_PIPE_PATH."/params_Z";
?>

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
<head>
<style>
	body {
	  background-color: #f5f5f5; 
	  color: #015C65;
	}

	a:link {color:#015C65; text-decoration:underline;}     /* unvisited link */
	a:visited {color:#015C65; text-decoration:underline;}  /* visited link */
	a:hover {color:#015C65; text-decoration:underline;}    /* mouse over link */
	a:active {color:#015C65; text-decoration:underline;}   /* selected link */

	input[type="button"] {
	  background-color: #015C65;
	  padding: 3px;
	  color: white;
	  border-color: #000000;
	  border-width: 1px;
	  border-style: solid
	}
</style>
<?php
	// GET FIELD SIZE FROM PARAMS FILE
	// establish inst code from prefix of filenames
	$handle = fopen("res.skycamfiles", "r");
	if ($handle) {
    		while (($buffer = fgets($handle, 4096)) !== false) {
        		$line = explode("_", $buffer);
			$line_cleaned = array_map('trim', $line);		// remove newlines, whitespace etc.
			$inst_code = $line_cleaned[0];
		}
    	}
   	if (!feof($handle)) {
        	echo "Error: unexpected fgets() fail\n";
    	}
    	fclose($handle);

	if ($inst_code == 'z') 
	{
		$THIS_ETC_PIPE_PARAMS_PATH = $ETC_PIPE_PARAMSZ_PATH;
	} else if ($inst_code == 't')
	{ 
		$THIS_ETC_PIPE_PARAMS_PATH = $ETC_PIPE_PARAMST_PATH;
	}

	// search parameters file for fieldsize field and pass to js
	$handle = fopen($THIS_ETC_PIPE_PARAMS_PATH, "r");
	if ($handle) {
    		while (($buffer = fgets($handle, 4096)) !== false) {
        		$line = explode("\t", $buffer);
			$line_cleaned = array_map('trim', $line);		// remove newlines, whitespace etc.
			$key = $line_cleaned[0]; $val = $line_cleaned[1];
			if ($key == "fieldSize")
				$fieldSize = $val;
		}
    	}
   	if (!feof($handle)) {
        	echo "Error: unexpected fgets() fail\n";
    	}
    	fclose($handle);

	echo "<script type=\"text/javascript\">\n"; 
	echo "\tvar fieldSize = ".$fieldSize.";\n"; 
	echo "</script>\n"; 

	// LOAD FILE DATA FOR GRAPHS
	// parse data.mollweide file
	$handle = fopen("data.mollweide", "r");
        $DATA_MOLLWEIDE = array();
	if ($handle) {
    		while (($buffer = fgets($handle, 4096)) !== false) {
        		$line = explode("\t", $buffer);
			$line_cleaned = array_map('trim', $line);		// remove newlines, whitespace etc.
			$this_data = array('ra_deg' 	=> $line_cleaned[0],
				       	   'dec_deg' 	=> $line_cleaned[1], 
				           'filter' 	=> 'r', 
				           'selected' 	=> 0
				          );
			array_push($DATA_MOLLWEIDE, $this_data);	
		}
    	}
   	if (!feof($handle)) {
        	echo "Error: unexpected fgets() fail\n";
    	}
    	fclose($handle);

	echo "<script type=\"text/javascript\">\n"; 
	echo "\tvar data_mollweide = new Array();\n"; 
	foreach($DATA_MOLLWEIDE as $key => $value) 
	{ 
		$json = json_encode($value, JSON_NUMERIC_CHECK );
		echo "\tdata_mollweide[".$key."] = ".$json.";\n"; 
	} 
	echo "</script>\n"; 

	// parse data.calibration file
	$handle = fopen("data.calibration.subsample", "r");
        $DATA_CALIBRATION = array();
	if ($handle) {
    		while (($buffer = fgets($handle, 4096)) !== false) {
        		$line = explode("\t", $buffer);
			$line_cleaned = array_map('trim', $line);		// remove newlines, whitespace etc.
			$this_data = array('x' 	=> $line_cleaned[0],
				       	   'y' 	=> $line_cleaned[1]
				          );
			array_push($DATA_CALIBRATION, $this_data);
		}	
    	}

   	if (!feof($handle)) {
        	echo "Error: unexpected fgets() fail\n";
    	}
    	fclose($handle);

	echo "<script type=\"text/javascript\">\n"; 
	echo "\tvar data_calibration = new Array();\n"; 
	foreach($DATA_CALIBRATION as $key => $value) 
	{ 
		$json = json_encode($value, JSON_NUMERIC_CHECK);
		echo "\tdata_calibration[".$key."] = ".$json.";\n"; 
	} 
	echo "</script>\n"; 

	// parse data.calibration.fit file
	$handle = fopen("data.calibration.fit", "r");
        $DATA_CALIBRATION_FIT = array();
	if ($handle) {
    		while (($buffer = fgets($handle, 4096)) !== false) {
        		$line = explode("\t", $buffer);
			$line_cleaned = array_map('trim', $line);		// remove newlines, whitespace etc.
			$this_data = array('x' 	=> $line_cleaned[0],
				       	   'y' 	=> $line_cleaned[1]
				          );
			array_push($DATA_CALIBRATION_FIT, $this_data);
		}	
    	}

   	if (!feof($handle)) {
        	echo "Error: unexpected fgets() fail\n";
    	}
    	fclose($handle);

	echo "<script type=\"text/javascript\">\n"; 
	echo "\tvar data_calibration_fit = new Array();\n"; 
	foreach($DATA_CALIBRATION_FIT as $key => $value) 
	{ 
		$json = json_encode($value, JSON_NUMERIC_CHECK);
		echo "\tdata_calibration_fit[".$key."] = ".$json.";\n"; 
	} 
	echo "</script>\n"; 
?>
<script src="http://code.jquery.com/jquery-1.10.1.min.js"></script>
<script src="http://code.jquery.com/jquery-1.9.1.js"></script>
<script src="http://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
<script src="http://code.highcharts.com/highcharts.js"></script>
<script src="http://code.highcharts.com/modules/exporting.js"></script>
<script type="text/javascript">
function isPaneVisible(content)
{
	if ($(content).is(":hidden"))
		return false;
	else
		return true;
}

function togglePane(toggle, content)
{
	if (isPaneVisible(content))
	{
		$(toggle).html("<a href=\"" + toggle +"\">(show)</a>");
		$(content).css("display", "none");
	} else 
	{
		$(toggle).html("<a href=\"" + toggle +"\">(hide)</a>");
		$(content).css("display", "block");
	}
}

</script>
</head>
<body style="overflow-y: scroll;">
<?php include($WWW_PATH."/query_banner.php"); ?>
<div id="container" style="margin: 0 auto; width: 1100px; font-family: Verdana, Geneva, sans-serif;">
	<h1>Results</h1>
	<h3>Mollweide Projection <span id="mollweide_projection_toggle_pane"><a href="#mollweide_projection_toggle_pane">(hide)</a></span></h3>
   	<table style="width: 1100px;" id="mollweide_content"><tr><td colspan="5">
		 	<canvas id="map" style="z-index: 100; position: relative; border: 1px solid white; background-color: #FFFFFF;">
			<p>Your browser does not support canvas.</p>
        		</canvas>
		<tr><td style="width: 1px; text-align: left;">
		<div class="slider" id="slider-1">
			<input class="slider-input" id="slider-input-1" name="slider-input-1"/>
		</div>
		</td>
		<td style="width: 10px; text-align: left;">
		<div style="float: left; align: middle;">
			&nbsp;Rotation: <div id='vRotation' style='display: inline;'>0</div>&deg;
		</div>
		</td>
		<td style="width: 1px; text-align: left;">
    		<div class="slider" id="slider-2">
    			<input class="slider-input" id="slider-input-2" name="slider-input-2"/>
		</div>
		</td>
		<td style="width: 10px; text-align: left;">
		<div style="float: left;">
			&nbsp;Zoom: <div id='vZoom' style='display: inline;'>10</div>
		</div>
		</td>
		<td style="width: 50px; text-align: right;">
    			<input type="button" value="reset" onClick="javascript:useDefault();" title="Click to reset to default value">
		</td>
		</tr>
	</table>
    			
	<script type="text/javascript">
 		fields = new Array();
		values = new Array();
		for (var i = 0; i < data_mollweide.length; i++) {
			fields.push(data_mollweide[i]);
		}
	</script>

	<script type="text/javascript" src="<?php echo $WWW_JS_PATH; ?>/projection-map-read-only/javascript/slider/range.js"></script>
	<script type="text/javascript" src="<?php echo $WWW_JS_PATH; ?>/projection-map-read-only/javascript/slider/timer.js"></script>
	<script type="text/javascript" src="<?php echo $WWW_JS_PATH; ?>/projection-map-read-only/javascript/slider/slider.js"></script>
	<link type="text/css" rel="StyleSheet" href="<?php echo $WWW_JS_PATH; ?>/projection-map-read-only/javascript/slider/winclassic.css" />
	<script type="text/javascript" src="<?php echo $WWW_JS_PATH; ?>/projection-map-read-only/javascript/hammer.js"></script>
	<script type="text/javascript" src="<?php echo $WWW_JS_PATH; ?>/projection-map-read-only/javascript/map.js"></script>
	<script type="text/javascript">
		var projMap;
		window.onload = function() { projMap = new ProjectionMap( new MollweideProjection(), fieldSize); };
	</script>

	<script type="text/javascript">
	$("#mollweide_projection_toggle_pane").click(function(){
		togglePane("#mollweide_projection_toggle_pane", "#mollweide_content");
	});
	</script>

	<h3>Colour calibration plot <span id="colour_calibration_toggle_pane"><a href="#colour_calibration_toggle_pane">(hide)</a></span></h3>
	<div id="calibration_content"></div>
        <script type="text/javascript">
	Highcharts.setOptions({
		lang: {
			contextButtonTitle: "Chart options",
			loading: "Loading.."
		}
	});
	$('#calibration_content').highcharts({
		chart: {
			type: 'scatter',
			backgroundColor: '#f5f5f5',
			width: 1100,
			height: 600,
			zoomType: 'xy',
			animation:false
		},

		legend: {
			enabled: true
		},

		credits: {
			enabled: false
		},

		plotOptions: {
                        scatter: {
			    	turboThreshold: 0,	// this removes the limit on the amount of points allowed
				events: {
					legendItemClick: function(event) {
					}
				}
			},
			line: {
			}
		},

		tooltip: {
    			backgroundColor: '#FFFFFF',
    			borderColor: 'black',
    			borderRadius: 2,
    			borderWidth: 1,
			formatter: function() {
       				return '<b>B-R: </b>' + this.x + '<br>' + '<b>R<sub>inst</sub> - R<sub>cat</sub>: </b>' + this.y
			},
                        hideDelay: 400,
    			animation:false
		},

		title: {
			text: '',
			style: {
				color: '#015C65'
			},	
			x: -20
		},

		xAxis: {
    			title: {
        			text: "B-R",
				style: {
					color: '#015C65'
				},
				offset: 30
    			},
    			labels: {
				style: {
					color: '#015C65'
				}
    			},
			gridLineWidth: 1,
			gridLineColor: 'grey',
			startOnTick: true,
			endOnTick: true,
			lineColor: '#000000',
			lineWidth: 1,
			min: -1,
			max: 4
		},

		yAxis: {
    			title: {
        			text: "R<sub>inst</sub> - R<sub>cat</sub>",
				style: {
					color: '#015C65'
				},
				offset: 40
    			},
    			labels: {
				style: {
					color: '#015C65'
				}
    			},
			gridLineWidth: 1,
			gridLineColor: 'grey',
			startOnTick: true,
			endOnTick: true,
			lineColor: '#000000',
			lineWidth: 1

		},

		exporting: {
            		buttons: {
				contextButton: {
					enabled: false
				}
			}
		},

		series: [{
			'type': 'scatter',
			'data': data_calibration,
			'name': 'data',
			'visible' : false,
			'color': '#910000',
			'zIndex': -1
		},
		{
			'type': 'line',
			'data': data_calibration_fit,
			'name': 'best fit',
			'visible' : true
		}
		]

	});
	</script>

	<script type="text/javascript">
	$("#colour_calibration_toggle_pane").click(function(){
		togglePane("#colour_calibration_toggle_pane", "#calibration_content");
	});
	</script>

	<h3>Log	<span id="log_toggle_pane"><a href="#log_toggle_pane">(show)</a></span></h3>
	<div id="log_content" style="display: none; margin:0 auto; padding: 5px; text-align: left; width: 1100px; font-family: inherit; font-size: 0.8em; line-height: 1.5em; border-color: black; border-width: 1px; border-style: solid; background-color: white; ">
        <?php 
                $logContents = file_get_contents("res.log");
                print nl2br($logContents);
        ?>
      	</div>

	<script type="text/javascript">
	$("#log_toggle_pane").click(function(){
		togglePane("#log_toggle_pane", "#log_content");
	});
	</script>

	<br/>
</div>
<br/>
</body>
</html>
