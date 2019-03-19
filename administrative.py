import gettext
_ = gettext.gettext

# DCS: Edit Server Info
MOTD = _("""
Message Of The Day:
422d server will be testing the backend software on the server in the next few months.
Due to the instability of the current DCS World build, the server are likely to crash at some point, or merely stop to work at all.
If <F.10 Other> option failed to show up in the radio menu, or static aircrafts on the apron do not de-spawn, it might be the backend software lost connection with DCS World server.
Please understand that these issues might be common before Eagle Dynamics implements the new Dedicated Server.

And we wish you a Happy New Year 2019!

12/29/2018
""")

RULES = _("""
Server Basic Rule:
1. Since this server is still in testing phase, the rule is not that strict.
2. Avoid team kill as much as possible. You might be auto-banned by the server backend.
""")

FAQ = _("""
Q: What this is server for? Is it PvE or PvP or what?
A: This is a server hosted by Virtual 422d Test and Evaluation Squadron. Our aim is to provide a multi-player based test environment for weapons and aircrafts in DCS World.
We use a backend software to retrieve data from and interact with DCS World server. This server is also intended to provide a training environment for 422d TES. During training sessions the server will be passworld protected.

Q: What kind of features does this server offer?
A: One of the most important feature is the server backend's capability to integrate and interpret different kinds of information from different sources.
In general, DCS World data are obtained through Export, Control API or Mission. A lua server is built in each of these three environment. Therefore, the server can easily query DCS for a more detailed picture of a specific unit or player.
For instance, through the net table in Control API, the server will be able to see what language version is a new connected user is using; however, this kind of information is not accessible from Mission environment.
When the backend has access to all three environment, it is rather easy to customize the message locale and system of measurement for different client language.

Q: I have interest in joining 422d TES?
A: This squadron is invited only for the time being. 
""")
# DCS: Edit Server Info End
