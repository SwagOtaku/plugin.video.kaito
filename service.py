# -*- coding: utf-8 -*-
from resources.lib.ui import maintenance
from resources.lib.ui import database_sync

database_sync.AnilistSyncDatabase()
maintenance.run_maintenance()
