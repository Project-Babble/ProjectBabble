
![Babble Logo](https://github.com/SummerSigh/ProjectBabble/blob/SummerSigh-patch-4/Babble.png?raw=true)

<h3 align="center">
Project Babble is an open-source mouth tracking project designed to work with any VR headset. We strive to make our models robust to different lighting, cameras, image qualities and facial structures!
</h3>

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Links](#links)
  
## Features
- 100% open-source! 🌟
- Fast and robust! 🚀
- Works with existing blendshape standards! ⚙️
- Constantly updated and modified! 🔧

## Installation
### Windows
Head to the releases section and [download the latest installer](https://github.com/Project-Babble/ProjectBabble/releases/latest).

### Linux
Copy, paste and run the following script into the terminal of your choice:

```bash
bash -c "$(curl -fsSL https://gist.githubusercontent.com/dfgHiatus/a92a3caae24c1bfab1c7544537a654c5/raw/494a4bc5ed6c97745c7a283661d2f5530ba3d949/project-babble-install.sh)"
```

Once it's finished installing, you can update and run the Babble app by typing `babble-app` into your terminal.

*You should also be able to run the Windows executable through Wine!*

#### Note:
If you recieve a `ModuleNotFoundError: No module named 'tkinter'` error message on run, you'll need to install `tkinter` for your distro.

For Ubuntu or other distros with apt:
```bash
sudo apt-get install python3-tk
```
For Fedora:
```bash
sudo dnf install python3-tkinter
```

You can read more about this [here](https://stackoverflow.com/questions/25905540/importerror-no-module-named-tkinter).

## Usage 
We have integrations for [VRChat](https://docs.babble.diy/docs/software/integrations/vrc), [Resonite](https://docs.babble.diy/docs/software/integrations/resonite) and [ChilloutVR](https://docs.babble.diy/docs/software/integrations/chilloutVR)!

Looking for something else? Check out our [documentation](https://docs.babble.diy/)!

## Links
- [Our Discord](https://discord.gg/XAMZmjBktk)
- [Our Twitter](https://x.com/projectBabbleVR)
- [Wandb Runs](https://wandb.ai/summerai/ProjectBabble)