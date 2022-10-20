<?php

    ini_set("display_error", "stderr");

    function print_help(){

        print("NAPOVEDA\n");
        
    }

    function handle_arguments( $arguments ){
        
        $parameters = array(
            "help" => false,
            "directory" => false,
            "directory_path" => ".",
            "recursive" => false,
            "parse_script" => false,
            "parse_file" => "parse.php",
            "int_script" => false,
            "int_file" => "interpret.py",
            "parse_only" => false,
            "int_only" => false,
            "jexampath" => false,
            "jexampath_path" => "/pub/courses/ipp/jexamxml/",
            "noclean" => false
        );

        if( count( $arguments ) !== 0 ){

            foreach( $arguments as $argument ){

                // Get argument's prefix
                $argument_prefix = substr( $argument, 0, 2 );
    
                // If argument contains "="
                if( strpos($argument, "=") !== false ){
    
                    // Get argument's name
                    $argument_name = substr( $argument, 2, strpos( $argument, "=" ) - 2 );

                    // Get argument's value
                    $argument_value =  substr( $argument, strpos( $argument, "=" ) + 1 );

                }else{
    
                    // Get argument's name
                    $argument_name = substr( $argument, 2 );
    
                }
    
                if( $argument_prefix != "--" ){
                    
                    fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" );
                    exit(10);
    
                }

                switch( $argument_name ){

                    case "help":

                        if( $parameters["directory"] or $parameters["recursive"] or $parameters["parse_script"] or $parameters["int_script"] or $parameters["parse_only"] or $parameters["int_only"] or $parameters["jexampath"] or $parameters["noclean"] )
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["help"] = true;
                        break;
                    
                    case "directory":

                        if( $parameters["help"] )
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["directory"] = true;
                        if( !isset($argument_value) ){ fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["directory_path"] = $argument_value;
                        break;

                    case "recursive":

                        if( $parameters["help"] )
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["recursive"] = true;
                        break;

                    case "parse-script":

                        if( $parameters["help"] or $parameters["int_only"] )
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["parse_script"] = true;
                        if( !isset($argument_value) ){ fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["parse_file"] = $argument_value;
                        break;

                    case "int-script":

                        if( $parameters["help"] or $parameters["parse_only"] )
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["int_script"] = true;
                        if( !isset($argument_value) ){ fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["int_file"] = $argument_value;
                        break;

                    case "parse-only":

                        if( $parameters["help"] or $parameters["int_only"] or $parameters["int_script"] )
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["parse_only"] = true;
                        break;

                    case "int-only":

                        if( $parameters["help"] or $parameters["parse_only"] or $parameters["parse_script"] or $parameters["jexampath"])
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["int_only"] = true;
                        break;

                    case "jexampath":

                        if( $parameters["help"] or $parameters["int_only"] )
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["jexampath"] = true;
                        if( !isset($argument_value) ){ fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["jexampath_path"] = $argument_value;
                        break;

                    case "noclean":

                        if( $parameters["help"] )
                        { fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" ); exit(10); }
                        $parameters["noclean"] = true;
                        break;

                    default:

                        fwrite( STDERR, "Zly parameter skriptu alebo zla kombinacia parametrov skriptu.\n" );
                        exit(10);
                        break;

                }
    
            }
    

        }

        // Return list of program parameters
        return $parameters;

    }

    class TestsController {

        public $tests = array();

        function scan_for_tests( $program_parameters, $dir ){

            // Check directory is valid
            if( !is_dir( $dir ) ){

                fwrite( STDERR, "Zadany adresar neexistuje alebo sa neda otvorit.\n" );
                exit(41);

            }

            // Get files of the directory
            $files = scandir( $dir );

            // Remove "." directory from array of files
            if( ($key = array_search(".", $files) ) !== false ){

                unset( $files[$key] );

            }

            // Remove ".." directory from array of files
            if( ( $key = array_search("..", $files) ) !== false ){

                unset( $files[$key] );

            }

            // For every file in the directory
            foreach( $files as $file ){

                // If file is an another directory
                if( is_dir( $dir . "/" . $file ) ){

                    // If script should search for tests recursively
                    if( $program_parameters["recursive"] ){

                        $this->scan_for_tests( $program_parameters, $dir . "/" . $file );

                    }

                }else{

                    // Divide file into fileinfo
                    $file_info = pathinfo($file);

                    // If file has "src" extension
                    if( $file_info["extension"] == "src" ){

                        # Create a new test
                        $new_test = new Test( $dir, $file_info["filename"] );

                        // Save the new test
                        array_push( $this->tests, $new_test );
                        
                        // Run the new test
                        $new_test->run($program_parameters);

                    }

                }

            }

        }

        function print_tests(){

            $test_number = 1;

            foreach( $this->tests as $test ){

                ?>

                <tr>
                    <td><?php echo $test_number?></td>
                    <td><?php echo $test->name?></td>
                    <td><?php echo $test->dir?></td>
                    <?php
                    
                        if( $test->result == "passed" ){
                            ?><td style="color:green">prešiel</td><?php
                        }else{
                            ?><td style="color:red">neprešiel</td><?php
                        }
                    ?>
                </tr>

                <?php

                // Increase test number
                $test_number = $test_number + 1;

            }

        }

    }

    class Test {

        public $dir;
        public $name;
        public $result;

        function __construct( $dir, $name ){

            $this->dir = $dir;
            $this->name = $name;

        }

        function run( $program_parameters ){

            // Define needed paths
            $src_path = "{$this->dir}/{$this->name}.src";
            $in_path = "{$this->dir}/{$this->name}.in";
            $out_path = "{$this->dir}/{$this->name}.out";
            $rc_path = "{$this->dir}/{$this->name}.rc";
            $tmp_parse_out_path = "{$this->dir}/{$this->name}.parse.out.tmp";
            $tmp_int_out_path = "{$this->dir}/{$this->name}.int.out.tmp";

            // Define needed variable
            $idk2 = null;
            $result_code = null;

            // Check if .in file exists
            if( !file_exists( $in_path ) ){

                $in_file = fopen($in_path, "w");
                fclose($in_file);

            }

            // Check if .out file exists
            if( !file_exists( $out_path ) ){

                $out_file = fopen($out_path, "w");
                fclose($out_file);

            }

            // Check if .rc file exists
            if( !file_exists($rc_path) ){

                $rc_file = fopen($this->dir . '/' . $this->name . '.rc', "w");

                // Write 0 to file
                fwrite($rc_file,"0");

            }

            if( $program_parameters["parse_only"] ){

                // Do only test for parse.php
                exec("php8.1 {$program_parameters["parse_file"]} < {$src_path} > {$tmp_parse_out_path}", $idk2, $result_code);

                // If parse.php finished  work without error
                if( $result_code == 0 ){

                    // Do comparison with jexamxml
                    exec("java -jar {$program_parameters["jexampath_path"]}jexamxml.jar {$out_path} {$tmp_parse_out_path}", $idk2, $result_code);

                    // Decide if out files are different
                    if( $result_code == 0 ){

                        $this->result = "passed";

                    }else{

                        $this->result = "failed";

                    }

                }else{

                    // If parse.php finished work with error
                    // Check if error codes match
                    if( $result_code == intval( file_get_contents($rc_path) ) ){

                        $this->result = "passed";

                    }else{

                        $this->result = "failed";

                    }

                }

            }elseif( $program_parameters["int_only"] ){

                // Do only test for interpret.py
                exec("python3.8 {$program_parameters["int_file"]} --source={$src_path} < {$in_path} > {$tmp_int_out_path}", $idk2, $result_code);

                // If interpret finished work without error
                if( $result_code == 0 ){

                    // Do diff for output files
                    exec("diff {$out_path} {$tmp_int_out_path}", $idk2, $result_code);

                    // Check if output files match
                    if( $result_code == 0 ){

                        $this->result = "passed";
                        
                    }else{

                        $this->result = "failed";
                    }

                }else{

                    // If interpret.py finished work with error
                    // Check if error codes match
                    if( $result_code == intval( file_get_contents($rc_path) ) ){

                        $this->result = "passed";

                    }else{

                        $this->result = "failed";

                    }

                }

            }else{

                // Run parse.php first
                exec("php8.1 {$program_parameters["parse_file"]} < {$src_path} > {$tmp_parse_out_path}", $idk2, $result_code);

                // If parse.py finished work without error
                if( $result_code == 0 ){

                    // Run interpret.py with source located in previouse generated output - $tmp_parse_out_path
                    exec("python3.8 {$program_parameters["int_file"]} --source={$tmp_parse_out_path} < {$in_path} > {$tmp_int_out_path}", $idk2, $result_code);

                    // If interpret finished work without error
                    if( $result_code == 0 ){

                        // Do diff for output files
                        exec("diff {$out_path} {$tmp_int_out_path}", $idk2, $result_code);

                        // Check if output files match
                        if( $result_code == 0 ){

                            $this->result = "passed";
                            
                        }else{

                            $this_result = "failed";
                        }

                    }else{

                        // If interpret.py finished work with error
                        // Check if error codes match
                        if( $result_code == intval( file_get_contents($rc_path) ) ){

                            $this->result = "passed";

                        }else{

                            $this->result = "failed";

                        }

                    }

                }else{

                     // If parse.py finished work with error
                    // Check if error codes match
                    if( $result_code == intval( file_get_contents($rc_path) ) ){

                        $this->result = "passed";

                    }else{

                        $this->result = "failed";

                    }

                }

            }

            if( !$program_parameters["noclean"] ){

                if( file_exists($tmp_parse_out_path) ){
                    unlink($tmp_parse_out_path);
                }

                if( file_exists($tmp_int_out_path) ){
                    unlink($tmp_int_out_path);
                }

            }

        }

    }

    $idk = array_shift( $argv );

    // Get the program parameters after handling arguments
    $program_parameters = handle_arguments( $argv );

    // Write help if requested
    if( $program_parameters["help"]){

        print_help();
        exit(0);

    }

    $test_controller = new TestsController();

    $test_controller->scan_for_tests( $program_parameters, $program_parameters["directory_path"] );

?>
<html>
    <head lang="sk">
        <title>Vysledok testov</title>
        <meta charset="UTF-8">
        <style>
            body {
                margin:0px;
            }
            h1 {
                margin:0px;
                padding:10px;
                padding-top:20px;
                width:100%;
            }
            h4 {
                margin:0px;
                padding:10px;
            }
            table {
                width:100%;
                border-collapse:collapse;
            }
            table th {
                padding:10px;
                border-bottom:2px solid #c5c5c5;
                border-collapse:collapse;
            }
            table td {
                padding:10px;
                border-bottom:1px dashed #c5c5c5;
            }
            table tr:hover td {
                background-color:#f1f1f1;
            }
        </style>
    </head>
    <body>
        <h1>Výsledok testov</h1>
        <?php

            $total_tests = 0;
            $passed_tests = 0;
            $failed_tests = 0;

            foreach( $test_controller->tests as $test ){

                $total_tests = $total_tests + 1;

                if( $test->result == "passed" ){

                    $passed_tests = $passed_tests + 1;

                }else{

                    $failed_tests = $failed_tests + 1;

                }

            }

        ?>
        <h4>Vykonaných testov: &nbsp&nbsp&nbsp&nbsp<?php echo $total_tests ?></h4>
        <h4>Úspešných testov: &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp<?php echo $passed_tests ?></h4>
        <h4>Neúspešných testov: &nbsp&nbsp<?php echo $failed_tests ?></h4>
        <br />
        <table>
            <tr style="text-align:left">
                <th>Číslo testu</th>
                <th>Názov testu</th>
                <th>Cesta</th>
                <th>Výsledok</th>
            </tr>
            <?php

                $test_controller->print_tests();

            ?>
        </table>
    </body>
</html>