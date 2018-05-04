<!DOCTYPE html>
<html lang="ru">
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <script type="text/javascript" src="//tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/2.2.0/jquery.min.js"></script>
    <script type="text/javascript" src="//tools-static.wmflabs.org/cdnjs/ajax/libs/twitter-bootstrap/3.3.6/js/bootstrap.min.js"></script>	
	<link rel="stylesheet" href="//tools-static.wmflabs.org/cdnjs/ajax/libs/twitter-bootstrap/3.3.6/css/bootstrap.min.css">
    <link rel="stylesheet" type="text/css" href="css/index.css">
	<noscript>
	    В вашем браузере отключён JavaScript.
	</noscript>
	<?php include 'oauth.php'; ?>
    <title>Отчёты мониторинга</title>
</head>
<body>

<?php
session_start();
if ( !isset($_SESSION["userName"]) ) {
	if ( $_GET['errorauth'] == 'blocked' ) {
		session_write_close();
		echo "<div class='auth_warning' align=center>Ваша учётная запись заблокирована в русской Википедии.<br>В доступе отказано.</div>";
		exit();
	}
	if ( $_GET['errorauth'] == 'rights' ) {
		session_write_close();
		echo "<div class='auth_warning' align=center>У вас недостаточно прав.<br>В доступе отказано.</div>";
		exit();
	}
	
	echo "
	<div class='welcome' align=center>Добро пожаловать!<br>
	Для работы в системе необходимо авторизироваться.</div>     
    <div class='btn-start' align=center>
	    <a role='button' href='https://tools.wmflabs.org/iluvatarbot/oauth.php?action=authorize' class='btn btn-primary btn-lg'> Авторизация<sup><small>*</small></sup></a>
	</div>
	<div align=center>
	    <sup><small>*</small></sup><font size='1'>Критерием допуска является наличие как минимум флага патрулирующего в русской Википедии.</font></div>
	</div>";
	session_write_close();
	exit();
}
session_write_close();
?>

<div class="header_bar">
    <div id="btn-back" class="btn_back"><a href='https://tools.wmflabs.org/iluvatarbot/'><span class='glyphicon glyphicon-chevron-left'></span></a></div>
    <div id='btn-logout' class='btn_logout'><?php session_start(); echo $_SESSION["userName"]; session_write_close(); ?> <a href='https://tools.wmflabs.org/iluvatarbot/oauth.php?action=logout'><span class='glyphicon glyphicon-log-out'></span></a></div>
</div><br>
<?php
$ts_pw = posix_getpwuid(posix_getuid());
# получаем реквизиты БД и админтокен (он же бототокен)
$ts_mycnf = parse_ini_file($ts_pw['dir'] . "/replica.my.cnf");
$admintoken = parse_ini_file($ts_pw['dir'] . "/pyBot/bottoken.ini");
$db = mysql_connect('tools.labsdb', $ts_mycnf['user'], $ts_mycnf['password']);
unset($ts_mycnf, $ts_pw);
mysql_select_db('s51092_raports', $db);
mysql_set_charset("utf8");

$query = "DELETE FROM `atokens` WHERE UNIX_TIMESTAMP('tokentime') < UNIX_TIMESTAMP()-24*60*60";
mysql_query( $query );

$atoken = md5(rand(0, PHP_INT_MAX).uniqid().rand(0, PHP_INT_MAX));
$query = "INSERT INTO `atokens` (`ajaxtoken`) VALUES ('".strval($atoken)."')";
mysql_query( $query );

$query = "SELECT * FROM `sources` ORDER BY `time` DESC";
$result_sources = mysql_query ( $query );

$query = "SELECT * FROM `templates` ORDER BY `type`";
$result_templates = mysql_query ( $query );

$query = "SELECT * FROM `fem` ORDER BY `time` DESC";
$result_fem = mysql_query ( $query );

mysql_close ($db);
?>

<div class='caption_s' align=center>Добавленные сомнительные источники</div>
<div id="table_sources" class="table_sources">
<?php
if ( mysql_num_rows($result_sources) != 0 ) {
    echo "<div class='table_marg'>
	<table class='table table-border'>
            <thead class='thead'><tr>
            <th scope='col'>Страница</th>
            <th scope='col'>Причина</th>
            <th scope='col'>Участник</th>
            <th scope='col'>Дата</th>
            <th scope='col'>Отметить</th>
        </tr></thead>
        <tbody>";
    while($row_sources = mysql_fetch_array($result_sources)) {
        echo "
		<tr class='label-s-".$row_sources[oldid]."-".$row_sources[diff]."'>";
        if ($row_sources[diff] != 0) {
            echo "<td class='t_start' valign='middle'><a href='https://ru.wikipedia.org/w/index.php?title=".rawurlencode($row_sources[title])."&oldid=".$row_sources[oldid]."&diff=".$row_sources[diff]."'>".$row_sources[title]."</a></td>";
        }
        else {
            echo "<td class='t_start' valign='middle'><a href='https://ru.wikipedia.org/w/index.php?oldid=".$row_sources[oldid]."'>".$row_sources[title]."</a></td>";
        }
        echo "
			<td class='t_body'><font class='rcolor'>".$row_sources[reason]."</font></td>
			<td class='t_body'><a href='https://ru.wikipedia.org/wiki/Special:Contribs/".rawurlencode($row_sources[user])."'>".$row_sources[user]."</a></td>
			<td class='t_body'>".date('d.m.Y', strtotime($row_sources[time]))."</td>
			<td class='t_end active'><label id='btn-s-".$row_sources[oldid]."-".$row_sources[diff]."' class='t_btn'><span class='glyphicon glyphicon-ok icolor'></span></label></td>
        </tr>
            <script>
                jQuery(document).ready(function() {
                jQuery('#btn-s-".$row_sources[oldid]."-".$row_sources[diff]."').click(function () {
                    jQuery('.label-s-".$row_sources[oldid]."-".$row_sources[diff]."').hide('slow');
                    jQuery.post('remove.php', { type: 'sources', oldid: '".strval($row_sources[oldid])."', diff: '".strval($row_sources[diff])."', ajaxtoken: '".strval($atoken)."' } );
                }); });
		    </script>";
    }
    echo "
		</tbody>
	</table>
</div>\n";
}
?>
</div>

<div class='caption_t' align=center>Некорректно размещённые номинационные шаблоны</div>
<div id="table_templates" class="table_templates">
<?php
if ( mysql_num_rows($result_templates) != 0 ) {
	echo "<div class='table_marg'>
	<table class='table table-border'>
        <thead><tr>
            <th scope='col'>Страница</th>
            <th scope='col'>Целевая страница</th>
            <th scope='col'>Отметить</th>
        </tr></thead>
        <tbody>";
    $i = 0;
    while($row_templates = mysql_fetch_array($result_templates)) {
        if ( strval($row_templates[link]) == '0' ) {
            $target_page = '<i>неизвестно</i>';
			}
        $i++;
        echo "
		<tr class='label-t-".$i."'>
		    <td class='t_start' valign='middle'><a href='https://ru.wikipedia.org/wiki/".rawurlencode($row_templates[title])."'>".$row_templates[title]."</a>";
        if ( strval($row_templates[link]) == '0' ) {
            echo "
			<td class='t_body'>".$target_page."</td>";
        }
        else {
            echo "
			<td class='t_body'><a href='https://ru.wikipedia.org/wiki/".strval($row_templates[link])."'>".strval($row_templates[link])."</a></td>";
        }
        echo "
			<td class='t_end active'><label id='btn-t-".$i."' class='t_btn'><span class='glyphicon glyphicon-ok icolor'></span></label></td>
        </tr>
			   <script>
                jQuery(document).ready(function() {
                jQuery('#btn-t-".$i."').click(function () {
                    jQuery('.label-t-".$i."').hide('slow');
                    jQuery.post('remove.php', { type: 'templates', title: '".rawurlencode(strval($row_templates[title]))."', link: '".rawurlencode(strval($row_templates[link]))."', stype: '".strval($row_templates[type])."', ajaxtoken: '".strval($atoken)."' } );
                }); });
			   </script>";
    }
    echo "
		</tbody>
	</table>
</div>\n";
}
?>
</div>

<div class='caption_f' align=center>Добавленные феминитивы</div>
<div id="table_fem" class="table_fem">
<?php
if ( mysql_num_rows($result_fem) != 0 ) {
    echo "<div class='table_marg'>
	<table class='table table-border'>
            <thead><tr>
            <th scope='col'>Страница</th>
            <th scope='col'>Причина</th>
            <th scope='col'>Участник</th>
            <th scope='col'>Дата</th>
            <th scope='col'>Отметить</th>
        </tr></thead>
        <tbody>";
    while($row_fem = mysql_fetch_array($result_fem)) {
        echo "
		<tr class='label-f-".$row_fem[oldid]."-".$row_fem[diff]."'>";
        if ($row_fem[diff] != 0) {
            echo "<td class='t_start' valign='middle'><a href='https://ru.wikipedia.org/w/index.php?title=".rawurlencode($row_fem[title])."&oldid=".$row_fem[oldid]."&diff=".$row_fem[diff]."'>".$row_fem[title]."</a></td>";
        }
        else {
            echo "<td class='t_start' valign='middle'><a href='https://ru.wikipedia.org/w/index.php?oldid=".$row_fem[oldid]."'>".$row_fem[title]."</a></td>";
        }
        echo "
			<td class='t_body'><font class='rcolor'>".$row_fem[reason]."</font></td>
			<td class='t_body'><a href='https://ru.wikipedia.org/wiki/Special:Contribs/".rawurlencode($row_fem[user])."'>".$row_fem[user]."</a></td>
			<td class='t_body'>".date('d.m.Y', strtotime($row_fem[time]))."</td>
			<td class='t_end active'><label id='btn-f-".$row_fem[oldid]."-".$row_fem[diff]."' class='t_btn'><span class='glyphicon glyphicon-ok icolor'></span></label></td>
        </tr>
            <script>
                jQuery(document).ready(function() {
                jQuery('#btn-f-".$row_fem[oldid]."-".$row_fem[diff]."').click(function () {
                    jQuery('.label-f-".$row_fem[oldid]."-".$row_fem[diff]."').hide('slow');
                    jQuery.post('remove.php', { type: 'fem', oldid: '".strval($row_fem[oldid])."', diff: '".strval($row_fem[diff])."', ajaxtoken: '".strval($atoken)."' } );
                }); });
		    </script>";
    }
    echo "
		</tbody>
	</table>
</div>\n";
}
?>
</div>

<div class="foot"><?php
session_start();
if ( $_SESSION["userName"] == 'Iluvatar' ) {
echo "
<div align='center'>
    <small>
        Админ: <a href='' id='admin-soursec'>АИ</a> / <a href='' id='admin-soursec7'>АИ7</a> / <a href='' id='admin-fem'>ФЕМ</a> / <a href='' id='admin-fem7'>ФЕМ7</a>
    </small>
</div>	 
	 <script>
         jQuery(document).ready(function() {
             jQuery('#admin-soursec').click(function () {
                 jQuery.post('remove.php', { adminaction: 'deletesources', ajaxtoken: '".strval($atoken)."', admintoken: '".strval($admintoken['bottoken'])."' } );
                 alert('Таблица сомнительных источников очищена полностью.')
				}); });
         jQuery(document).ready(function() {
             jQuery('#admin-fem').click(function () {
                 jQuery.post('remove.php', { adminaction: 'deletefem', ajaxtoken: '".strval($atoken)."', admintoken: '".strval($admintoken['bottoken'])."' } );
                 alert('Таблица феминитивов очищена полностью.')
				}); });
         jQuery(document).ready(function() {
             jQuery('#admin-sources7').click(function () {
                 jQuery.post('remove.php', { adminaction: 'deletesources7', ajaxtoken: '".strval($atoken)."', admintoken: '".strval($admintoken['bottoken'])."' } );
                 alert('Записи старше 7 дней удалены из таблицы сомнтельных источников.')
				}); });
         jQuery(document).ready(function() {
             jQuery('#admin-fem7').click(function () {
                 jQuery.post('remove.php', { adminaction: 'deletefem7', ajaxtoken: '".strval($atoken)."', admintoken: '".strval($admintoken['bottoken'])."' } );
                 alert('Записи старше 7 дней удалены из таблицы феминитивов.')
				}); });
	</script>";
}
session_write_close();
?></div>

<div align=center>
    <div id='work' class="work">
        <h3>Выберите нужный отчёт</h3>
        <div class="button btn-group-vertical" data-toggle="buttons">
		<?php
		    if ( mysql_num_rows($result_sources)!= 0 ) {
                echo "<label class='btn btn-default' id='work_sources'>Мониторинг размещения сомнительных источников <span class='badge badge-danger' id='badge-sources'>".mysql_num_rows($result_sources)."</span></label>
			    <script>
				    jQuery(document).ready(function() {
                        jQuery('#work_sources').click(function () {
                            jQuery('#work').hide();
				            jQuery('#btn-back').css('display', 'inline-block');
							jQuery('.foot').css('display', 'block');
							jQuery('.caption_s').css('display', 'block');
                            jQuery('#table_sources').css('display', 'block');
                    }); });
				</script>";
			}
			else {
				echo "
			<label class='btn btn-default disabled' id='work_sources'>Мониторинг размещения сомнительных источников</label>";
			}
			
			if (mysql_num_rows($result_templates)!= 0 ) {
				echo "
			<label class='btn btn-default' id='work_templates'>Мониторинг корректности размещения номинационных шаблонов <span class='badge' id='badge-templates'>".mysql_num_rows($result_templates)."</span></label>
                <script>
				    jQuery(document).ready(function() {
						jQuery('#work_templates').click(function () {
						    jQuery('#work').hide();
							jQuery('#btn-back').css('display', 'inline-block');
							jQuery('.foot').css('display', 'block');
							jQuery('.caption_t').css('display', 'block');
                            jQuery('#table_templates').css('display', 'block');
						}); });			
                 </script>";
			}
			else {
				echo "
			<label class='btn btn-default disabled' id='work_templates'>Мониторинг корректности размещения номинационных шаблонов</label>";
			}
            
			if (mysql_num_rows($result_fem)!= 0 ) {
				echo "
			<label class='btn btn-default' id='work_fem'>Мониторинг феминитивов <span class='badge' id='badge-fem'>".mysql_num_rows($result_fem)."</span></label>
			    <script>
				    jQuery(document).ready(function() {
			            jQuery('#work_fem').click(function () {
                            jQuery('#work').hide();
							jQuery('#btn-back').css('display', 'inline-block');
							jQuery('.foot').css('display', 'block');
							jQuery('.caption_f').css('display', 'block');
                            jQuery('#table_fem').css('display', 'block');
						});});
			    </script>";
			}
			else {
				echo "
			<label class='btn btn-default disabled' id='work_fem'>Мониторинг феминитивов</label>
			";
			}
        ?>
        </div>
    </div>
</div>
</body>
</html>