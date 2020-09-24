_name_map_ = {"terminal_returner": "terminal"}


def terminal_returner(data, **kwargs):
    """Returner that prints results to terminal"""
    # add colouring
    if "colour" in kwargs:
        from colorama import init

        init()
        R = "\033[0;31;40m"  # RED
        G = "\033[0;32;40m"  # GREEN
        Y = "\033[0;33;40m"  # Yellow
        # B = "\033[0;34;40m" # Blue
        N = "\033[0m"  # Reset
        fttr = "{}{}{}"  # formatter
        # get colour words from output
        red_words = kwargs.get(
            "red",
            "False,No,Failed,Error,Failure,Fail,false,no,failed,error,failure,fail",
        )
        green_words = kwargs.get("green", "True,Yes,Success,Ok,true,yes,success,ok")
        yeallow_words = kwargs.get("yellow", "Warning,warning")
        # convert colour words to lists
        red_words = [i.strip() for i in red_words.split(",")]
        green_words = [i.strip() for i in green_words.split(",")]
        yeallow_words = [i.strip() for i in yeallow_words.split(",")]
        # add colouring to output
        for red_word in red_words:
            data = data.replace(red_word, fttr.format(R, red_word, N))
        for green_word in green_words:
            data = data.replace(green_word, fttr.format(G, green_word, N))
        for yeallow_word in yeallow_words:
            data = data.replace(yeallow_word, fttr.format(Y, yeallow_word, N))
    # print output
    if _ttp_["python_major_version"] is 2:
        if isinstance(data, str) or isinstance(data, unicode):
            print(data)
        else:
            print(str(data).replace("\\n", "\n"))
    elif _ttp_["python_major_version"] is 3:
        if isinstance(data, str):
            print(data)
        else:
            print(str(data).replace("\\n", "\n"))
