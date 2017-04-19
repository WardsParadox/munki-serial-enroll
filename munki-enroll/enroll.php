<?php
namespace CFPropertyList;
// require cfpropertylist
require dirname(__FILE__) . '/CFPropertyList/classes/CFPropertyList/CFPropertyList.php';

function writemanifest($outputplist,$inputschool,$inputdisplayname,$inputuser,$inputnotes){
  $plist = new CFPropertyList();
  $plist->add($dict = new CFDictionary());
  $plistnew = $outputplist;
  echo "Writing new plist: " . $plistnew . PHP_EOL;

  // Add Default Catalog
  $dict->add('catalogs', $array = new CFArray());
  $array->add(new CFString('Main'));

  $dict->add('included_manifests', $array = new CFArray());
  $array->add(new CFString($inputschool));

  $dict->add('display_name', new CFString($inputdisplayname));

  $dict->add('user', new CFString($inputuser));

  $dict->add('notes', new CFString($inputnotes));

  $plist->save($plistnew,CFPropertyList::FORMAT_XML,$formatted=true);
}
//print_r($_GET); //dignosing which variables make it to server
if((isset($_GET["serial"])) AND (isset($_GET["displayname"])) AND (isset($_GET["school"])) AND (isset($_GET["notes"])) AND (isset($_GET["user"]))){

$serial = $_GET["serial"];
$school = $_GET["school"];
$displayname = $_GET["displayname"];
$user = $_GET["user"];
$notes = $_GET["notes"];

$destination = '/path/to/munki/repo/manifests' . $serial;
//$destination = dirname(__FILE__) . '/testmanifest';

    if (file_exists($destination)){

  // Check for override key
      if (isset($_GET['override']) AND filter_var($_GET['override'],FILTER_VALIDATE_BOOLEAN)){
          echo "Removing old manifest, and recreating: " . $destination . PHP_EOL;
          unlink($destination);
          writemanifest($destination,$school,$displayname,$user,$notes);
          exit(0);
    }
      else{
          echo "Manifest exists! Override not set!" . PHP_EOL;
          exit(1);
        }
    }
    else{
      writemanifest($destination,$school,$displayname,$user,$notes);
      exit(0);
    }
  }
else{
  echo "Missing Variable(s). Please send all variables!" . PHP_EOL;
  exit(2);
  }

?>
