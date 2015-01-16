<script type="text/javascript">
function toggleDatabaseFlags()
{
	if (isDatabaseInsertSet())
	{
		$('#formcontrols_dbflags').slideDown();
		$('#dbclobber').attr('disabled', false);
		$('#dboverwrite').attr('disabled', false);
		
	} else
	{
		$('#formcontrols_dbflags').slideUp();
		$('#dbclobber').attr('disabled', true);
		$('#dboverwrite').attr('disabled', true);
	}
} 

function isDatabaseInsertSet()
{
	if ($('#senddbquery').is(':checked') == true)
		return true;
	else
		return false;
} 
</script>

<form id="formcontrols" action="" method="POST">
	<!-- instrument -->
	<h3 style="text-align: left;">Instrument</h3>
	<hr class="controls_separator"/>
	<br/>
	<div style="width:100%; text-align:right">
		<input id="skycamT" type="radio" name="inst" value="SkyCamT" <?php if ( (isset($_POST['inst']) && $_POST['inst'] == "SkyCamT") ) { echo 'checked="true"'; } ?> >SkycamT</input>&nbsp;&nbsp;<label for="skycamT"></label>
		<br/>
		<input id="skycamZ" type="radio" name="inst" value="SkyCamZ" <?php if ( (!isset($_POST['inst'])) || (isset($_POST['inst']) && $_POST['inst'] == "SkyCamZ") ) { echo 'checked="true"'; } ?> >SkycamZ</input>&nbsp;&nbsp;<label for="skycamZ"></label>

		<br/><br/>
	</div>

	<!-- dates -->  
	<h3 style="text-align: left;">Query dates</h3>   
	<hr class="controls_separator"/>
	<br/>
	<div style="width:100%; text-align:right">
		<table style="font-size: inherit; width: 100%; text-align: inherit;">
			<tr><td style="text-align: right; width: 40px;">From</td><td><input id="datefrom" class="tb1" type="text" name="datefrom" value="<?php if (isset($_POST['datefrom'])) { echo substr($_POST['datefrom'], 0, -3); } else { echo '2013-06-10 23:45'; } ?>"></input></td></tr>
       		<tr><td style="text-align: right;">To</td><td ><input id="dateto" class="tb1" type="text" name="dateto" value="<?php if (isset($_POST['dateto'])) { echo substr($_POST['dateto'], 0, -3); } else { echo '2013-06-10 23:59'; } ?>"></input></td></tr>
		</table>
		<script type="text/javascript">
		$(function(){
			$('*[name=datefrom]').appendDtpicker({
				"dateFormat": "YYYY-MM-DD hh:mm:00",
				"minuteInterval": 15,
			});
			$('*[name=dateto]').appendDtpicker({
				"dateFormat": "YYYY-MM-DD hh:mm:00",
				"minuteInterval": 15,
			});
		});
		</script>
	</div>

	<!-- database -->
	<h3 style="text-align: left;">Database</h3>   
	<hr class="controls_separator"/>
	<br/>
	<div style="width:100%; text-align:right">
		<input type="checkbox" name="senddbquery" id="senddbquery" onClick="toggleDatabaseFlags();" <?php if (isset($_POST['senddbquery'])) { echo "checked"; } ?> >send results to database</input>&nbsp;&nbsp;<label for="senddbquery"></label><br/>
		<div id="formcontrols_dbflags" style="display: none;">
			<input type="radio" name="dbclobber" id="dbclobber" value="ignore" <?php if (!isset($_POST['senddbquery'])) { echo "disabled='disabled'"; } ?> <?php if ( (!isset($_POST['dbclobber'])) || (isset($_POST['dbclobber']) && $_POST['dbclobber'] == "ignore") ) { echo 'checked="true"'; } ?> >ignore</input>&nbsp;&nbsp;<label for="dbclobber"></label><br/>
			<input type="radio" name="dbclobber" id="dboverwrite" value="overwrite" <?php if (!isset($_POST['senddbquery'])) { echo "disabled='disabled'"; } ?> <?php if ( (isset($_POST['dbclobber']) && $_POST['dbclobber'] == "overwrite") ) { echo 'checked="true"'; } ?> >overwrite</input>&nbsp;&nbsp;<label for="dboverwrite"></label>
		</div>
	</div>

	<!-- submit -->  
	<br/><br/>
	<div style="width:100%; text-align:right">
       	 	<input type="hidden" name="process" value=1></input>
		<input type="button" value="go!" id="formcontrols_submit" onClick="
		if (isResultPaneVisible()) { 
			$('#result_content').slideUp('slow', function() {
				$('#formcontrols').submit();
			});
		} else {
			$('#formcontrols').submit();
		}
		"/>
	</div>
</form>

<!-- need to ascertain if database flags should be collapsed or not on form submit -->
<?php
if (isset($_POST['process']) && ($_POST['process'] == true))
{
	if (isset($_POST['senddbquery']) && ($_POST['senddbquery']) == true)
	{
	?>
	<script type="text/javascript">
		$('#formcontrols_dbflags').show();
	</script>
	<?php
	}
}
?>
