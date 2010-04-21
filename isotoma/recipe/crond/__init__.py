# Copyright 2010 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from stat import S_IXUSR, S_IXGRP, S_IXOTH

class Cron(object):

    def __init__(self, buildout, name, options):
        self.name = name
        self.options = options
        self.buildout = buildout

        self.scriptdir = os.path.join(self.buildout['buildout']['parts-directory'], self.name)

        self.options.setdefault("location", "cron.d")

        self.options.setdefault("minute", "*")
        self.options.setdefault("hour", "*")
        self.options.setdefault("day-of-month", "*")
        self.options.setdefault("month", "*")
        self.options.setdefault("day-of-week", "*")

        if self.options.get("script") and self.options.get("command"):
            raise ValueError("You can't pass a script and specify a command to run")

        if not self.options.get("user"):
            raise ValueError("You must specify a user to run the command as")

        flag = True
        for o in ("at", "minute", "hour", "day-of-month", "month", "day-of-week"):
            if self.options.get(o) != "*":
                flag = False

        if flag:
            raise ValueError("You must set one of 'at', 'minute', 'hour', 'day-of-month', 'month' or 'day-of-week'")

    def install(self):
        installed = []

        if not os.path.isdir(self.options['location']):
            os.makedirs(self.options['location'])

        script_path = None
        if self.options.get("script"):
            if not os.path.isdir(self.scriptdir):
                os.makedirs(self.scriptdir)

            script_path = os.path.join(self.scriptdir, "script")
            f = open(script_path, "w")
            f.write(self.options["script"])
            f.close()

            os.chmod(script_path, os.stat(script_path)[0] | S_IXUSR | S_IXGRP | S_IXOTH)

            installed.append(script_path)

        path = os.path.join(self.options['location'], self.name)
        file = open(path, 'w')

        # Can specify optional "comments" for any ops user looking in cron.d
        comments = self.options.get("comments", "").split("\n")
        if comments:
            for comment in comments:
                if not comment:
                    continue
                file.write("# %s\n" % comment)
            file.write("\n")

        # Users can specify environment variables
        vars = self.options.get("environment-vars", "").split("\n")
        if vars:
            for var in vars:
                if not var:
                    continue
                kv = var.split()
                file.write("%s=%s\n" % tuple(kv))
            file.write("\n")

        if self.options.get("at"):
            rule = "@%s" % self.options["at"]
        else:
            rule = "%(minute)s %(hour)s %(day-of-month)s %(month)s %(day-of-week)s" % self.options

        rule = rule + " " + self.options['user'].strip() + " "

        if script_path:
            rule = rule + script_path
        else:
            rule = rule + self.options['command'].strip().replace("\n", " ")

        file.write(rule)
        file.close()

        installed.append(path)

        return installed

    def update(self):
        pass

