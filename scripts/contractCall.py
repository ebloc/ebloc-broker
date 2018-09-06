import subprocess, os

# ex: contractCalls('isUserExist.py', [userID])
def contractCalls_check_output(call, args): #{
   return subprocess.check_output([contractCallPath + '/' + call] + args).decode('utf-8').strip()    
   # subprocess.Popen([contractCallPath + '/' + call] + args,
   #                       stdout=subprocess.PIPE,
   #                       universal_newlines=True).communicate()[0].strip()
#}

# cmd: ps aux | grep \'[D]river.py\' | grep \'python\' | wc -l
def contractCalls(call, a1, a2, a3): #{
    contractCallPath = 'contractCalls' 
    return subprocess.Popen([contractCallPath + '/' + call, a1, a2, a3],
                            stdout=subprocess.PIPE,
                            universal_newlines=True).communicate()[0].strip() 

#}

userInfo = contractCalls('getUserInfo.py', '0x4e4a0750350796164d8defc442a712b7557bf282', 1, 2).replace(" ", "")
print(userInfo)
