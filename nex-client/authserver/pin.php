 
<form method="GET">
	<input type="text" value="Pin" name="pin" id="pin" />
	<!-- <input type="text" value="key" name="hwid" id="hwid" /> -->
	<input type="submit" value="Activate !" name="test"  />
</form>


<?php
if(isset($_GET['test'])) {
	$key = $_GET['pin'];
	$filename = 'list.txt';
	
	$lines = file($filename); // reads a file into a array with the lines
	$output = '';

	foreach ($lines as $line) {
		if (!strstr($line, $key . "\n")) {
			$output .= $line;
		} else {
			// echo "<h1>" . $line . "</h1>";
			// PIN EXIST !!!!!
			echo "verified";
			// Now add a new random unique pin
			$newPin = rand(10000, 99999);

			// Check if this pin already exist.
    		while(strpos($filename, $newPin) === true) {
				// echo "Pin already exist !";
				$newPin = rand(10000, 99999);
			}

			// echo "<h1>New pin : " . $newPin . "</h1>";
			$output = $output . $newPin . "\n";
		}
	}
	// replace the contents of the file with the output
	file_put_contents($filename, $output);
}
?>