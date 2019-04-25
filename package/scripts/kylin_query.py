import os
import base64
from time import sleep
import pwd
import grp
from resource_management import *


class KylinQuery(Script):

    def install(self, env):
        import params
        self.install_packages(env)
        env.set_params(params)
        # Create user and group for kylin if they don't exist
        try:
            grp.getgrnam(params.kylin_group)
        except KeyError:
            Group(group_name=params.kylin_group)

        try:
            pwd.getpwnam(params.kylin_user)
        except KeyError:
            User(username=params.kylin_user,
                 gid=params.kylin_group,
                 groups=[params.kylin_group],
                 ignore_failures=True
                 )
        Directory([params.install_dir],
                  mode=0755,
                  cd_access='a',
                  create_parents=True
                  )
        Execute('cd ' + params.install_dir + '; wget ' +
                params.downloadlocation + ' -O kylin.tar.gz  ')
        Execute('cd ' + params.install_dir + '; tar -xvf kylin.tar.gz')
        Execute('cd ' + params.install_dir +
                ';rm -rf latest; ln -s apache-kylin* latest')
        cmd = format("chown -R {kylin_user}:{kylin_group} {install_dir}")
        Execute(cmd)

    def configure(self, env):
        import params
        env.set_params(params)
        kylin_properties = InlineTemplate(params.kylin_properties)
        File(format("{install_dir}/latest/conf/kylin.properties"),
             owner=params.kylin_user,
             group=params.kylin_group,
             content=kylin_properties)

        File(format("{tmp_dir}/kylin_init.sh"),
             owner=params.kylin_user,
             group=params.kylin_group,
             content=Template("init.sh.j2"),
             mode=0o700
             )
        File(format("{tmp_dir}/kylin_env.rc"),
             owner=params.kylin_user,
             group=params.kylin_group,
             content=Template("env.rc.j2"),
             mode=0o700
             )
        Execute(format("bash {tmp_dir}/kylin_init.sh"), user=params.kylin_user)

    def start(self, env):
        import params
        env.set_params(params)
        self.configure(env)
        Execute(format(
            ". {tmp_dir}/kylin_env.rc;{install_dir}/latest/bin/kylin.sh start;cp -rf {install_dir}/latest/pid /var/run/kylin.pid"), user=params.kylin_user)

    def stop(self, env):
        import params
        env.set_params(params)
        self.configure(env)
        Execute(
            format(". {tmp_dir}/kylin_env.rc;{install_dir}/latest/bin/kylin.sh stop"), user=params.kylin_user)

    def restart(self, env):
        self.stop(env)
        self.start(env)

    def status(self, env):
        check_process_status("/var/run/kylin.pid")


if __name__ == "__main__":
    KylinQuery().execute()
