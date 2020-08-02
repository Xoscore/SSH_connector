# SSH_connector
Exercise for Evolution Gaming

The task was to implement class with required parameters and methods
So, I do it through Fabric
It was too simple, because Fabric do most of works
So, I add console argparser, and now you can not only import and use this class, but also use it from console as standalone app
It was also a way to test this thing for works

You can use my AWS machine to test, if you want
Here example of call:
$python remcmd.py -H ec2-18-217-38-138.us-east-2.compute.amazonaws.com -u test_ssh -p test123 -c "ls -lah" -v

The most tough thing here, was take the PID of process, which instanly finish
So, it's a crutch - I add echo of PID in the moment of command execution, and get PID as first line of output

Another problem in terminate
Even Fabric not work asyncronly, it make session and wait for output
So, when output is done, process already dead
It is possible, to make another session from same user, to kill process of first one
But in Terminal, first session wait for output to done anyway, and second session possible to start only from another terminal, which does not get access to first session PID
I implement it anyway, but without additional info, I do not know what way to use it, it raise exception "process not found" every time

Well, I hope this is good enough to show my skills
