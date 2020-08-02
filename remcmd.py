# coding=utf-8
"""Command execution over SSH"""
# I will use fabric here
from fabric import connection
# But still, Fabric use Paramiko exceptions class to throw
from paramiko import ssh_exception
from invoke import exceptions
# Make some pretty console interface, so this class either can be imported or run separately
import argparse

debug = False
print_statistic = False


def main():
    # Collect input options
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command", default=None, type=str, required=True,
                        help="Input Linux command to execute")
    parser.add_argument("-H", "--host", default=None, type=str, required=True,
                        help="Ip address of remote host")
    parser.add_argument("-u", "--user", default=None, type=str, required=True,
                        help="Username to execute command")
    # For password, if it not passed, client will try to use environment ssh keys to connect
    parser.add_argument("-p", "--password", default=None, type=str, required=False,
                        help="Password for user")
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help="increase output verbosity")
    args = parser.parse_args()
    # It is not necessary, but I want to show how I can make it
    # Debug here will print both exceptions, the custom and the prent from ssh_exceptions
    # By default all calls are silent
    # So, print_statistic will print data, for each method call
    global debug
    global print_statistic
    if args.verbosity >= 2:
        debug = True
        print_statistic = True
    elif args.verbosity >= 1:
        print_statistic = True
    else:
        pass
    # This for console work example
    rc = RemoteCommand(args.command, args.host, args.user, args.password)
    rc.run()
    rc.get_pid()
    rc.get_output()
    rc.get_exit_code()


class RemoteCommandException(Exception):
    pass


class RemoteCommand:
    def __init__(self, command, ssh_host, ssh_user, ssh_password=None):
        """Initialize RemoteCommand object

        :param command: Command to execute on remote host
        :param ssh_host: Remote host (IP address or domain name)
        :param ssh_user: Remote username
        :param ssh_password: password for authentication to remote host (optional in case SSH agent is used)

        Example usage:

            >>> rc = RemoteCommand("cat /proc/cmdline", "1.1.1.1", "john", "supersecretpassword")
            >>> rc.run()
            >>> rc.get_get_pid()
            >>> rc.get_result()
        """
        self.command = command
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password

        # Because we not use connect method separately, I think that client object should be connected on create

        # If password not provided, this one will try to use system host keys to connect
        # Well, I spent some time to realize how ssh_keys works in Fabric
        # But it is not clear still, mostly because of my Win machine are lack of them
        # Seems like it hide everything under hood and manage them automaticly
        # And it takes too long to real checks
        # Well, I will not implement connect by keys here (anyway it is not part of excercise)
        # If so, it can be manage by environments, but I do not know what machine it will running for
        # Still, some hosts allow to connect without password, so I pass the None
        if self.ssh_password is None:
            connect_options = {}
        else:
            connect_options = {"password": ssh_password}
        # Fabric not throw exceptions here, on connect he only create workers
        # So, I should catch them on run instead
        self.client = connection.Connection(ssh_host, user=ssh_user, connect_kwargs=connect_options)
        # To keep result of command execution
        self.result = None
        # To keep terminate result separately
        self.kill = None
        if print_statistic:
            print("Connect to host: " + self.ssh_host + "\nWith user: " + self.ssh_user )

    def run(self) -> None:
        """Execute command on remote host

        :raises: `RemoteCommandException` if command execution is not successful (for instance: command is not found)
        """
        # Cause only way to guarantee get PID is on run, I add this additions here
        # I try several ways with paramiko, but it locks until process not return output
        # To do not implement my own multiprocess (it will be too complicated here), I found Fabric
        # Which actually just high-level cover for Paramiko
        try:
            # By default it print result at moment, so hide it here and call later
            if print_statistic:
                print("Run command: " + self.command)
            self.result = self.client.run(self.command + " & echo $!", hide=True)
        except ssh_exception.SSHException as e:
            if debug:
                raise RemoteCommandException(str(e))
            raise RemoteCommandException(str(e)) from None
        # Here just check if error happens
        if not self.result.ok:
            raise RemoteCommandException(self.result.stderr)

    def get_pid(self) -> int:
        """Get PID (process ID) of executed command"""
        # There is several ways - 'jobs -p' return all processes
        # But we need to get pid of only last one
        # It is possible to use ps aux, but it can catch wrong process
        # On top of that, some commands run very quick, so PID can be destroyed at time of asking
        # So, the only way to guarantee get pid of process - is to ask it on initial command execution

        # Because every command in Linux get PID on run, no need additional checks here
        # If it not run, exception will throw in execution
        # Because I call process PID on execution, first line is always PID
        if print_statistic:
            print("PID of process: " + self.result.stdout.split('\n')[0])
        return int(self.result.stdout.split('\n')[0])

    def terminate(self) -> None:
        """Terminate running command

        :raises: `RemoteCommandException` if command cannot be terminated for some reason
        """
        # To terminate process, just send kill to it's PID
        pid = self.get_pid()
        try:
            self.kill = self.client.run("kill " + str(pid), hide=True)
            # If this command fails, exception comes from Invoke, not Paramiko
        except (ssh_exception.SSHException, exceptions.UnexpectedExit) as e:
            if debug:
                raise RemoteCommandException(str(e))
            raise RemoteCommandException(str(e)) from None
        # Here just check if error happens
        if not self.kill.ok:
            raise RemoteCommandException(self.result.stderr)
        if print_statistic:
            print("Process with " + str(pid) + " was killed with status " + self.kill.return_code)

    def get_output(self) -> str:
        """Return command generated output"""
        # Fabric do everything here himself
        if print_statistic:
            print("Execution output: " + "\n".join(self.result.stdout.split('\n')[1:]))
        return "\n".join(self.result.stdout.split('\n')[1:])

    def get_exit_code(self) -> int:
        """Return command exit code"""
        # Again, Fabric already do all the stuff
        if print_statistic:
            print("Result code: " + str(self.result.return_code))
        return self.result.return_code


if __name__ == "__main__":
    main()

