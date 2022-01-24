#!/usr/bin/env python3

"""UNIX: enable executable from terminal with: chmod +x filename."""

if __name__ == "__main__":
    import call

    from broker.utils import run

    # import logging
    # import multiprocessing as mp
    # mp.log_to_stderr(logging.DEBUG)

    filename = call.__file__
    func_name = "getDataStoreDuration"
    data = (
        "",
        "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49",
        "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49",
        "QmdxhbcHJr3r4yeJNdvRabLVJ78VT2DTNMkBD7LN2MzeqJ",
    )

    output = run(["python", filename, *[str(arg) for arg in data]])
    print(output)
    # # in case filename is an executable you don't need "python" before `filename`:
    # try:
    #     # for breakpoint remove , stdout=subprocess.PIPE
    #     p = subprocess.Popen(args=["python", filename, *[str(arg) for arg in data]], stdout=subprocess.PIPE)
    #     output, error = p.communicate()
    #     p.wait()
    #     time.sleep(1)
    #     if output:
    #         output = output.strip().decode("utf-8")
    #     print(output)
    # except:
    #     breakpoint()  # DEBUG
    #     pass
