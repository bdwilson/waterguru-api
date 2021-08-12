# WaterGuru Simple REST API

There is no authentication because the expectation is that you're running this on your internal, trusted home network. You've been warned.

<b>Please do not abuse the WaterGuru API - this should not be run more than once or twice a day. It is not intended to be run more often as it does not
properly implement a token refresh option.</b> <i>(Hint, hint, please add this
and send me a pull request)</i>

# Installation (Docker)
1. Grab the [Dockerfile](https://raw.githubusercontent.com/bdwilson/waterguru-api/master/Dockerfile) via wget and put it in a directory on your Docker server. Then run the commands
below from that directory
2. <code> # docker build -t waterguru-api --build-arg WG_USER='your@email.address' --build-arg WG_PASS='your_password' .</code> __Don't forget the dot at the end!__ CTRL-C out of it when it's complete
Optional arguments are WG_PORT. You will need to use your email and
password that you use with the WaterGuru app already. These will default to us, na,
and 53255.
3. Run your newly created image: <code> # docker run -d --restart unless-stopped -p 53255:53255 --name waterguru-api -t waterguru-api</code> (if you changed the port when you built your image, you should also change it here)
4. That's it. If you need to troubleshoot your docker image, you can get into
it via:
<code> # docker exec -it waterguru-api /bin/bash</code> or 
<code># docker run -it waterguru-api /bin/bash</code> and then poke around and

# Usage
You'll need to get the IP address of your docker host, then navigate to: <i>http://your.ip.address:53255/api/wg></i> - this should show you json output from WaterGuru

# Hubitat
Coming Soon. 

Bugs/Contact Info
-----------------
Bug me on Twitter at [@brianwilson](http://twitter.com/brianwilson) or email me [here](http://cronological.com/comment.php?ref=bubba).
