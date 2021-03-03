 
<form method="POST">
	<input type="password" svalue=""  name="passwrd" id="passwrd" />
	<input type="submit" value="Get a pin !" name="submit"  />
</form>


<?php
if (isset($_POST['passwrd'])) {

	if ($_POST['passwrd'] == "NexPass6543") {
		$lines = file('list.txt');
		$line = $lines[rand(0, count($lines) - 2)];
		echo $line;
	}
}
?>