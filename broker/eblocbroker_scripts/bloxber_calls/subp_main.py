#!/usr/bin/env python3

if __name__ == "__main__":
    import call

    from broker._utils.tools import run

    fn = call.__file__
    func_name = "getStorageInfo"
    data = (
        "",
        "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49",
        "0xD118b6EF83ccF11b34331F1E7285542dDf70Bc49",
        "QmdxhbcHJr3r4yeJNdvRabLVJ78VT2DTNMkBD7LN2MzeqJ",
    )

    output = run(["python", fn, *[str(arg) for arg in data]])
    print(output)
    # # in case fn is an executable you don't need "python" before `fn`:
    # try:
    #     # for breakpoint remove , stdout=subprocess.PIPE
    #     p = subprocess.Popen(args=["python", fn, *[str(arg) for arg in data]], stdout=subprocess.PIPE)
    #     output, error = p.communicate()
    #     p.wait()
    #     time.sleep(1)
    #     if output:
    #         output = output.strip().decode("utf-8")
    #     print(output)
    # except:
    #     breakpoint()  # DEBUG
    #     pass
