<?php
/**
 * Written in 2013 by Brad Jorsch
 *
 * To the extent possible under law, the author(s) have dedicated all copyright
 * and related and neighboring rights to this software to the public domain
 * worldwide. This software is distributed without any warranty.
 *
 * See <http://creativecommons.org/publicdomain/zero/1.0/> for a copy of the
 * CC0 Public Domain Dedication.
 */

// ******************** CONFIGURATION ********************

/**
 * Set this to point to a file (outside the webserver root!) containing the
 * following keys:
 * - agent: The HTTP User-Agent to use
 * - consumerKey: The "consumer token" given to you when registering your app
 * - consumerSecret: The "secret token" given to you when registering your app
 */
$inifile = '/data/project/iluvatarbot/oauth.ini';

/**
 * Set this to the Special:OAuth URL.
 * Note that /wiki/Special:OAuth sometimes fails, while
 * index.php?title=Special:OAuth works fine.
 */
$mwOAuthUrl = 'https://ru.wikipedia.org/w/index.php?title=Special:OAuth';

/**
 * Set this to the interwiki prefix for the OAuth central wiki.
 */
$mwOAuthIW = 'ru';

/**
 * Set this to the API endpoint
 */
$apiUrl = 'https://ru.wikipedia.org/w/api.php';

// ****************** END CONFIGURATION ******************

// Setup the session cookie
session_name( 'iluvatarbot' );
$params = session_get_cookie_params();
session_set_cookie_params(
    $params['lifetime'],
    dirname( $_SERVER['SCRIPT_NAME'] )
);


// Read the ini file
$ini = parse_ini_file( $inifile );
if ( $ini === false ) {
    header( "HTTP/1.1 500 Internal Server Error" );
    echo 'The ini file could not be read';
    exit(0);
}
if ( !isset( $ini['agent'] ) ||
    !isset( $ini['consumerKey'] ) ||
    !isset( $ini['consumerSecret'] )
) {
    header( "HTTP/1.1 500 Internal Server Error" );
    echo 'Required configuration directives not found in ini file';
    exit(0);
}
$gUserAgent = $ini['agent'];
$gConsumerKey = $ini['consumerKey'];
$gConsumerSecret = $ini['consumerSecret'];

// Load the user token (request or access) from the session
$gTokenKey = '';
$gTokenSecret = '';
$userName ='';
session_start();
if ( isset( $_SESSION['tokenKey'] ) ) {
    $gTokenKey = $_SESSION['tokenKey'];
    $gTokenSecret = $_SESSION['tokenSecret'];
}
if ( isset( $_SESSION['userName'] ) ) {
    $userName = $_SESSION['userName'];
}
session_write_close();

// Fetch the access token if this is the callback from requesting authorization
if ( isset( $_GET['oauth_verifier'] ) && $_GET['oauth_verifier'] ) {
    fetchAccessToken();
}

// Take any requested action
switch ( isset( $_GET['action'] ) ? $_GET['action'] : '' ) {
    case 'authorize':
        doAuthorizationRedirect();
        break;

    case 'identify':
        doIdentify();
        break;
    case 'logout':
        logout();
        break;
}

function logout(){
    global $gTokenKey;
    session_start();
    unset($_SESSION['tokenKey']);
    unset($_SESSION['tokenSecret']);
    unset($_SESSION['userName']);
    session_write_close();
    unset($gTokenKey);
    unset($gTokenSecret);
    unset($userName);
    header("Location: https://tools.wmflabs.org/iluvatarbot");
}

function checklogin(){
    session_start();
    if (!isset($_SESSION["userName"])){
        echo "<h3> please <a href='login.php'>login</a> </h3>";
        session_write_close();
        exit(0);
    }
    session_write_close();
}

function getuserName(){
    session_start();
    $u  = $_SESSION["userName"];
    session_write_close();
    return $u;
}

// ******************** CODE ********************


/**
 * Utility function to sign a request
 *
 * Note this doesn't properly handle the case where a parameter is set both in
 * the query string in $url and in $params, or non-scalar values in $params.
 *
 * @param string $method Generally "GET" or "POST"
 * @param string $url URL string
 * @param array $params Extra parameters for the Authorization header or post
 * 	data (if application/x-www-form-urlencoded).R
 *В @return string Signature
 */
function sign_request( $method, $url, $params = array() ) {
    global $gConsumerSecret, $gTokenSecret;

    $parts = parse_url( $url );

    // We need to normalize the endpoint URL
    $scheme = isset( $parts['scheme'] ) ? $parts['scheme'] : 'http';
    $host = isset( $parts['host'] ) ? $parts['host'] : '';
    $port = isset( $parts['port'] ) ? $parts['port'] : ( $scheme == 'https' ? '443' : '80' );
    $path = isset( $parts['path'] ) ? $parts['path'] : '';
    if ( ( $scheme == 'https' && $port != '443' ) ||
        ( $scheme == 'http' && $port != '80' )
    ) {
        // Only include the port if it's not the default
        $host = "$host:$port";
    }

    // Also the parameters
    $pairs = array();
    parse_str( isset( $parts['query'] ) ? $parts['query'] : '', $query );
    $query += $params;
    unset( $query['oauth_signature'] );
    if ( $query ) {
        $query = array_combine(
        // rawurlencode follows RFC 3986 since PHP 5.3
            array_map( 'rawurlencode', array_keys( $query ) ),
            array_map( 'rawurlencode', array_values( $query ) )
        );
        ksort( $query, SORT_STRING );
        foreach ( $query as $k => $v ) {
            $pairs[] = "$k=$v";
        }
    }

    $toSign = rawurlencode( strtoupper( $method ) ) . '&' .
        rawurlencode( "$scheme://$host$path" ) . '&' .
        rawurlencode( join( '&', $pairs ) );
    $key = rawurlencode( $gConsumerSecret ) . '&' . rawurlencode( $gTokenSecret );
    return base64_encode( hash_hmac( 'sha1', $toSign, $key, true ) );
}

/**
 * Request authorization
 * @return void
 */
function doAuthorizationRedirect() {
    global $mwOAuthUrl, $gUserAgent, $gConsumerKey, $gTokenSecret;

    // First, we need to fetch a request token.
    // The request is signed with an empty token secret and no token key.
    $gTokenSecret = '';
    $url = $mwOAuthUrl . '/initiate';
    $url .= strpos( $url, '?' ) ? '&' : '?';
    $url .= http_build_query( array(
        'format' => 'json',

        // OAuth information
        'oauth_callback' => 'oob', // Must be "oob" for MWOAuth
        'oauth_consumer_key' => $gConsumerKey,
        'oauth_version' => '1.0',
        'oauth_nonce' => md5( microtime() . mt_rand() ),
        'oauth_timestamp' => time(),

        // We're using secret key signatures here.
        'oauth_signature_method' => 'HMAC-SHA1',
    ) );
    $signature = sign_request( 'GET', $url );
    $url .= "&oauth_signature=" . urlencode( $signature );
    $ch = curl_init();
    curl_setopt( $ch, CURLOPT_URL, $url );
    //curl_setopt( $ch, CURLOPT_SSL_VERIFYPEER, false );
    curl_setopt( $ch, CURLOPT_USERAGENT, $gUserAgent );
    curl_setopt( $ch, CURLOPT_HEADER, 0 );
    curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );
    $data = curl_exec( $ch );
    if ( !$data ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Curl error: ' . htmlspecialchars( curl_error( $ch ) );
        exit(0);
    }
    curl_close( $ch );
    $token = json_decode( $data );
    if ( is_object( $token ) && isset( $token->error ) ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Error retrieving token: ' . htmlspecialchars( $token->error );
        exit(0);
    }
    if ( !is_object( $token ) || !isset( $token->key ) || !isset( $token->secret ) ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Invalid response from token request';
        exit(0);
    }

    // Now we have the request token, we need to save it for later.
    session_start();
    $_SESSION['tokenKey'] = $token->key;
    $_SESSION['tokenSecret'] = $token->secret;
    session_write_close();

    // Then we send the user off to authorize
    $url = $mwOAuthUrl . '/authorize';
    $url .= strpos( $url, '?' ) ? '&' : '?';
    $url .= http_build_query( array(
        'oauth_token' => $token->key,
        'oauth_consumer_key' => $gConsumerKey,
    ) );
    header( "Location: $url" );
    echo 'Please see <a href="' . htmlspecialchars( $url ) . '">' . htmlspecialchars( $url ) . '</a>';
}

/**
 * Handle a callback to fetch the access token
 * @return void
 */
function fetchAccessToken() {
    global $mwOAuthUrl, $gUserAgent, $gConsumerKey, $gTokenKey, $gTokenSecret;

    $url = $mwOAuthUrl . '/token';
    $url .= strpos( $url, '?' ) ? '&' : '?';
    $url .= http_build_query( array(
        'format' => 'json',
        'oauth_verifier' => $_GET['oauth_verifier'],

        // OAuth information
        'oauth_consumer_key' => $gConsumerKey,
        'oauth_token' => $gTokenKey,
        'oauth_version' => '1.0',
        'oauth_nonce' => md5( microtime() . mt_rand() ),
        'oauth_timestamp' => time(),

        // We're using secret key signatures here.
        'oauth_signature_method' => 'HMAC-SHA1',
    ) );
    $signature = sign_request( 'GET', $url );
    $url .= "&oauth_signature=" . urlencode( $signature );
    $ch = curl_init();
    curl_setopt( $ch, CURLOPT_URL, $url );
    //curl_setopt( $ch, CURLOPT_SSL_VERIFYPEER, false );
    curl_setopt( $ch, CURLOPT_USERAGENT, $gUserAgent );
    curl_setopt( $ch, CURLOPT_HEADER, 0 );
    curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );
    $data = curl_exec( $ch );
    if ( !$data ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Curl error: ' . htmlspecialchars( curl_error( $ch ) );
        exit(0);
    }
    curl_close( $ch );
    $token = json_decode( $data );

    if ( is_object( $token ) && isset( $token->error ) ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Error retrieving token: ' . htmlspecialchars( $token->error );
        exit(0);
    }
    if ( !is_object( $token ) || !isset( $token->key ) || !isset( $token->secret ) ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Invalid response from token request';
        exit(0);
    }

    // Save the access token
    session_start();
    $_SESSION['tokenKey'] = $gTokenKey = $token->key;
    $_SESSION['tokenSecret'] = $gTokenSecret = $token->secret;
    session_write_close();

    doIdentify();
}


/**
 * Request a JWT and verify it
 * @return void
 */
function doIdentify() {
    global $mwOAuthUrl, $gUserAgent, $gConsumerKey, $gTokenKey, $gConsumerSecret, $userName;
    session_start();
    if (isset($_SESSION["userName"])){
        session_write_close();
		header("Location: https://tools.wmflabs.org/iluvatarbot");
    }
    session_write_close();
    $url = $mwOAuthUrl . '/identify';
    $headerArr = array(
        // OAuth information
        'oauth_consumer_key' => $gConsumerKey,
        'oauth_token' => $gTokenKey,
        'oauth_version' => '1.0',
        'oauth_nonce' => md5( microtime() . mt_rand() ),
        'oauth_timestamp' => time(),

        // We're using secret key signatures here.
        'oauth_signature_method' => 'HMAC-SHA1',
    );
    $signature = sign_request( 'GET', $url, $headerArr );
    $headerArr['oauth_signature'] = $signature;

    $header = array();
    foreach ( $headerArr as $k => $v ) {
        $header[] = rawurlencode( $k ) . '="' . rawurlencode( $v ) . '"';
    }
    $header = 'Authorization: OAuth ' . join( ', ', $header );

    $ch = curl_init();
    curl_setopt( $ch, CURLOPT_URL, $url );
    curl_setopt( $ch, CURLOPT_HTTPHEADER, array( $header ) );
    //curl_setopt( $ch, CURLOPT_SSL_VERIFYPEER, false );
    curl_setopt( $ch, CURLOPT_USERAGENT, $gUserAgent );
    curl_setopt( $ch, CURLOPT_HEADER, 0 );
    curl_setopt( $ch, CURLOPT_RETURNTRANSFER, 1 );
    $data = curl_exec( $ch );
    if ( !$data ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Curl error: ' . htmlspecialchars( curl_error( $ch ) );
        exit(0);
    }
    $err = json_decode( $data );
    if ( is_object( $err ) && isset( $err->error ) && $err->error === 'mwoauthdatastore-access-token-not-found' ) {
        // We're not authorized!
        echo 'You haven\'t authorized this application yet! Go <a href="' . htmlspecialchars( $_SERVER['SCRIPT_NAME'] ) . '?action=authorize">here</a> to do that.';
        echo '<hr>';
        return;
    }

    // There are three fields in the response
    $fields = explode( '.', $data );
    if ( count( $fields ) !== 3 ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Invalid identify response: ' . htmlspecialchars( $data );
        exit(0);
    }

    // Validate the header. MWOAuth always returns alg "HS256".
    $header = base64_decode( strtr( $fields[0], '-_', '+/' ), true );
    if ( $header !== false ) {
        $header = json_decode( $header );
    }
    if ( !is_object( $header ) || $header->typ !== 'JWT' || $header->alg !== 'HS256' ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Invalid header in identify response: ' . htmlspecialchars( $data );
        exit(0);
    }

    // Verify the signature
    $sig = base64_decode( strtr( $fields[2], '-_', '+/' ), true );
    $check = hash_hmac( 'sha256', $fields[0] . '.' . $fields[1], $gConsumerSecret, true );
    if ( $sig !== $check ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'JWT signature validation failed: ' . htmlspecialchars( $data );
        echo '<pre>'; var_dump( base64_encode($sig), base64_encode($check) ); echo '</pre>';
        exit(0);
    }

    // Decode the payload
    $payload = base64_decode( strtr( $fields[1], '-_', '+/' ), true );
    if ( $payload !== false ) {
        $payload = json_decode( $payload );
    }
    if ( !is_object( $payload ) ) {
        header( "HTTP/1.1 500 Internal Server Error" );
        echo 'Invalid payload in identify response: ' . htmlspecialchars( $data );
        exit(0);
    }

    session_start();
    $username = $payload -> username;
	$isblocked = $payload -> blocked;
	$usergroups = $payload -> groups;
    if ( ( in_array('sysop', $usergroups) ) OR ( in_array('closer', $usergroups) ) OR
	( in_array('engineer', $usergroups) ) OR ( in_array('editor', $usergroups) ) OR
	( in_array('checkuser', $usergroups) ) OR ( in_array('oversight', $usergroups) ) OR
	( in_array('bureaucrat', $usergroups) ) ) {
	    if ( $isblocked == '' ) {
			$_SESSION['userName'] = $username;
			session_write_close();
			header("Location: https://tools.wmflabs.org/iluvatarbot");
		}
		else {
		session_write_close();
		header("Location: https://tools.wmflabs.org/iluvatarbot?errorauth=blocked");
		}
	}
	else {
		session_write_close();
		header("Location: https://tools.wmflabs.org/iluvatarbot?errorauth=rights");
	}
}

