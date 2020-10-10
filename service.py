# -*- coding: utf-8 -*-

from resources.lib.ui import maintenance
from resources.lib.ui import database

database.build_tables()
maintenance.run_maintenance()
