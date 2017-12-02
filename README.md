# Synology Surveillance Station CLI

How it works:

```
> ./synology-ss.py home_mode
Home mode is off.
```

```
> ./synology-ss.py home_mode on
Home mode has been turned on.
```

```
> ./synology-ss.py camera 1 on
Camera 1 has been enabled.
```

```
> ./synology-ss.py cameras
ID   Camera         IP             State          Resolution
---  ------------   ------------   ------------   ------------
1    camera-2       10.0.1.60      enabled        1280x720
2    camera-1       10.0.1.59      enabled        1280x720
3    raspberry-pi   10.0.1.58      disabled       800x600
```

That's it!

# Configuring

Make sure you have a `config.json` file in the same directory as the script. A `config-template.json` is included in the repo:

```
{
  "username": "admin",
  "password": "",
  "url": "https://your-synology-nas.com:5001"
}
```

# Debugging

If something isn't working out, pass the `--debug` option to see what's going on.
