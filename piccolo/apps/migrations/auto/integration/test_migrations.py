import os
import shutil
import tempfile
import time
import typing as t
from unittest import TestCase

from piccolo.conf.apps import AppConfig
from piccolo.columns.column_types import Varchar
from piccolo.apps.migrations.commands.new import (
    _create_new_migration,
    _create_migrations_folder,
)
from piccolo.apps.migrations.commands.forwards import ForwardsMigrationManager
from piccolo.table import Table, create_table_class
from piccolo.utils.sync import run_sync


class TestMigrations(TestCase):
    def tearDown(self):
        create_table_class("MyTable").alter().drop_table(
            if_exists=True
        ).run_sync()

    def run_migrations(self, app_config: AppConfig):
        manager = ForwardsMigrationManager(app_name=app_config.app_name)
        run_sync(manager.create_migration_table())
        run_sync(manager.run_migrations(app_config=app_config))

    def _test_migrations(self, table_1: t.Type[Table], table_2: t.Type[Table]):
        temp_directory_path = tempfile.gettempdir()
        migrations_folder_path = os.path.join(
            temp_directory_path, "piccolo_migrations"
        )

        if os.path.exists(migrations_folder_path):
            shutil.rmtree(migrations_folder_path)

        _create_migrations_folder(migrations_folder_path)

        app_config = AppConfig(
            app_name="test_app",
            migrations_folder_path=migrations_folder_path,
            table_classes=[table_1],
        )

        meta = run_sync(
            _create_new_migration(app_config=app_config, auto=True)
        )
        self.assertTrue(os.path.exists(meta.migration_path))
        self.run_migrations(app_config=app_config)

        #######################################################################

        # It's kind of absurd sleeping for 1 microsecond, but it guarantees
        # the migration IDs will be unique, and just in case computers and / or
        # Python get insanely fast in the future :)
        time.sleep(1e-6)

        #######################################################################

        app_config.table_classes = [table_2]
        meta = run_sync(
            _create_new_migration(app_config=app_config, auto=True)
        )
        self.assertTrue(os.path.exists(meta.migration_path))
        self.run_migrations(app_config=app_config)

        # TODO - check the migrations ran correctly

    def test_add_column(self):
        table_1 = create_table_class("MyTable")
        table_2 = create_table_class(
            "MyTable", class_members={"name": Varchar()}
        )

        self._test_migrations(table_1=table_1, table_2=table_2)
