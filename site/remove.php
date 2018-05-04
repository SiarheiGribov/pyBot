<?php
header('Content-Type: text/html; charset=UTF-8');
$ts_pw = posix_getpwuid(posix_getuid());
$ts_mycnf = parse_ini_file($ts_pw['dir'] . "/replica.my.cnf");
$ts_filetoken = parse_ini_file($ts_pw['dir'] . "/pyBot/bottoken.ini");
$db = mysql_connect('tools.labsdb', $ts_mycnf['user'], $ts_mycnf['password']);
unset($ts_mycnf, $ts_pw);

mysql_select_db('s51092_raports', $db);
mysql_query("set_client='utf8'");
mysql_query("set character_set_results='utf8'");
mysql_query("set collation_connection='utf8_general_ci'");
mysql_query("SET NAMES 'utf8'");

if ( strval($_POST['bottoken']) == strval($ts_filetoken['bottoken']) ) {
	if ( strval($_POST['type']) == 'sources' ) {
	    $query = "INSERT INTO `sources` (`user`, `oldid`, `diff`, `title`, `reason`) VALUES ('".mysql_real_escape_string($_POST['user'])."', '".intval($_POST['oldid'])."', '".intval($_POST['diff'])."', '".mysql_real_escape_string($_POST['title'])."', '".mysql_real_escape_string($_POST['reason'])."')";
        $result = mysql_query ( $query );
	}
	if ( strval($_POST['type']) == 'templates' ) {
			$query = "SELECT `title` FROM `templates` WHERE ( title='".mysql_real_escape_string(urldecode($_POST['title']))."' AND link='".mysql_real_escape_string(urldecode($_POST['link']))."' AND type='".mysql_real_escape_string($_POST['stype'])."' )";
            $result = mysql_query ( $query );
			if (mysql_num_rows($result) == 0) {
	            $query = "INSERT INTO `templates` (`title`, `link`, `type`) VALUES ('".mysql_real_escape_string($_POST['title'])."', '".mysql_real_escape_string($_POST['link'])."', '".mysql_real_escape_string($_POST['stype'])."')";
	            $result = mysql_query ( $query );
	        }
	    }
	if ( strval($_POST['type']) == 'fem' ) {
	    $query = "INSERT INTO `fem` (`user`, `oldid`, `diff`, `title`, `reason`) VALUES ('".mysql_real_escape_string($_POST['user'])."', '".intval($_POST['oldid'])."', '".intval($_POST['diff'])."', '".mysql_real_escape_string($_POST['title'])."', '".mysql_real_escape_string($_POST['reason'])."')";
	    $result = mysql_query ( $query );
	}
	mysql_close ($db);
    exit;
}


$query = "SELECT `ajaxtoken` FROM `atokens` WHERE ajaxtoken='".mysql_real_escape_string($_POST['ajaxtoken'])."' AND UNIX_TIMESTAMP(`tokentime`) >= UNIX_TIMESTAMP()-24*60*60";
$result = mysql_query ( $query );
if (mysql_num_rows($result) == 0) {
    mysql_close ($db);
    exit;
}

if ($_POST['type'] == 'sources') {
    $query = "DELETE FROM `sources` WHERE oldid='".intval($_POST['oldid'])."' AND diff='".intval($_POST['diff'])."'";
    $result = mysql_query ( $query );
	}
if ($_POST['type'] == 'templates') {
        $query = "DELETE FROM `templates` WHERE ( title='".mysql_real_escape_string(urldecode($_POST['title']))."' AND link='".mysql_real_escape_string(urldecode($_POST['link']))."' AND type='".mysql_real_escape_string($_POST['stype'])."' )";
        $result = mysql_query ( $query );
	}
if ($_POST['type'] == 'fem') {
    $query = "DELETE FROM `fem` WHERE oldid='".intval($_POST['oldid'])."' AND diff='".intval($_POST['diff'])."'";
    $result = mysql_query ( $query );
	}
mysql_close ( $db);
?>