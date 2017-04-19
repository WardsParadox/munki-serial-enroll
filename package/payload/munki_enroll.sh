#!/bin/bash
shopt -s extglob
##### Tweak on the original Munki-Enroll
##### This has different logic based on whether the computer is a desktop or a laptop
##### If it's a laptop, the script grabs the user's full name
##### If it's a desktop, the script just grabs the computer's name
##### This version of the script also assumes you have an https-enabled Munki server with basic authentication
##### Change SUBMITURL's variable value to your actual URL
##### Also change YOURLOCALADMINACCOUNT if you have one

#######################
## User-set variables
# Change this URL to the location fo your Munki Enroll install
SUBMITURL="http://munki.example.com/munki-enroll/enroll.php"
# Change this to a local admin account you have if you have one
ADMINACCOUNT="YOURADMIN"
#######################

# Make sure there is an active Internet connection
SHORTURL=$(echo "$SUBMITURL" | awk -F/ '{print $3}')
PINGTEST=$(ping -o -t 4 "$SHORTURL")


if [ ! -z "$PINGTEST" ]; then
   # Always get the serial number
   SERIAL=$(/usr/sbin/system_profiler SPHardwareDataType | /usr/bin/awk '/Serial Number/ { print $4; }')

   # Get Model Identifier
   #MODEL=$(/usr/sbin/system_profiler SPHardwareDataType | /usr/bin/grep "Model Identifier" | awk -F ": " '{print $2}')
   # Get Model Description
   MODEL="$(/usr/libexec/PlistBuddy -c "Print :$(/usr/sbin/sysctl -n hw.model):_LOCALIZABLE_:marketingModel" /System/Library/PrivateFrameworks/ServerInformation.framework/Resources/English.lproj/SIMachineAttributes.plist | /usr/bin/sed 's/ /%20/g')"
   # Get the primary user
   PRIMARYUSER=''
   # This is a little imprecise, because it's basically going by process of     eimination, but that will pretty much work for the setup we have
    cd /Users || exit
    for u in *; do
       if [ "$u" != "Guest" ] && [ "$u" != "Shared" ] && [ "$u" != "root" ]&& [ "$u" != "$ADMINACCOUNT" ] && [ "$u" != "faculty" ] && [ "$u" != "administration" ]; then
            PRIMARYUSER="$u"
         fi
      done

      if [ "$PRIMARYUSER" != "" ]; then
         # Add real name (not just username) of user
         REALNAME="$(/usr/bin/dscl . -read /Users/"$PRIMARYUSER" dsAttrTypeStandard:RealName | /usr/bin/sed 's/RealName://g' | /usr/bin/tr '\n' ' ' | /usr/bin/sed 's/^ *//;s/ *$//' | /usr/bin/sed 's/ /%20/g')"
         if [ "$REALNAME" = "Teacher" ] || [ "$REALNAME" = "Generic" ]; then
            REALNAME="GenericAccount%20-%20Fix%20Later"
         fi
      else
         REALNAME="Undefined%20-%20Fix%20Later"
      fi
    DISPLAYNAME="$(/usr/sbin/scutil --get ComputerName | /usr/bin/sed 's/-/%2D/g' | /usr/bin/sed 's/ /%20/g')"
    CURSCHOOL=$(defaults read /Library/Preferences/ManagedInstalls ClientIdentifier)
    if [ "$CURSCHOOL" != "" ]; then
      if [[ "$CURSCHOOL" = *"Teacher" ]]; then
        echo "Replacing Teacher with Staff"
        SCHOOL="${CURSCHOOL/Teacher/Staff}"
      else
        SCHOOL="$CURSCHOOL"
      fi
    else
      SCHOOL="Staff"
    fi
   # Send information to the server to make the manifest
   /usr/bin/curl --max-time 5 -v --silent --get \
      -d displayname="$DISPLAYNAME" \
      -d serial="$SERIAL" \
      -d school="$SCHOOL" \
      -d user="$REALNAME" \
      -d notes="$MODEL" \
      "$SUBMITURL"
      #-d override="true" "$SUBMITURL"

   # Delete the ClientIdentifier, since we'll be using the serial number
    deleteClientIdentifier() {
      clientIdentifier=$(defaults read "$1" | grep "ClientIdentifier")
      if [ ! -z "$clientIdentifier" ]; then
        if [[ $EUID -ne 0 ]]; then
        sudo /usr/bin/defaults delete "$1" ClientIdentifier;
        else
          /usr/bin/defaults delete "$1" ClientIdentifier;
        fi
      fi
   }

   deleteClientIdentifier "/Library/Preferences/ManagedInstalls"

else
   # No good connection to the server
   echo "No Good Connection to Server"
   exit 1
fi
