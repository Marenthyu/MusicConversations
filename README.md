# MusicConversations
A Tool to let reactions be posted/spammed in Twitch Chat depending on an input text file

# Usage
This tool is built on and tested with Python 3.7 using pydle version 0.9.1.
To install the required requirements, use requirements.txt

For example, on windows with the py launcher:
```cmd
py -3 -m pip install -r requirements.txt
```
Configure it to your liking using ``musicconversations.cfg`` (feel free to copy ``musicconversations.cfg.sample`` and edit it from there);
Explanations of the options are in the sample file.

To start the Tool, launch ``musicConversations.py``, for example on windows with the py launcher:

```cmd
py -3 musicConversations.py
```

Debug logs will be kept as a ``debug.log`` file which will be rotated daily.

# Disclaimer
As per the ``LICENSE``, i am **NOT** liable for any damage or spamming occuring by using this tool.
You still require your own oauth tokens, which you can acquire on your own with other tools (or by doing the oauth dance yourself).