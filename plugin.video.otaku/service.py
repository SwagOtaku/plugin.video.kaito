# -*- coding: utf-8 -*-
from resources.lib.ui import maintenance
from resources.lib.ui import database_sync
from resources.lib.ui.globals import g
import sys

g.init_globals(sys.argv)
database_sync.AnilistSyncDatabase()
maintenance.run_maintenance()