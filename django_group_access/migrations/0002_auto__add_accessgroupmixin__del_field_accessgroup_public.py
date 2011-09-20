# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'AccessGroupMixin'
        db.create_table('access_accessgroupmixin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('access', ['AccessGroupMixin'])

        # Adding M2M table for field access_groups on 'AccessGroupMixin'
        db.create_table('access_accessgroupmixin_access_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('accessgroupmixin', models.ForeignKey(orm['access.accessgroupmixin'], null=False)),
            ('accessgroup', models.ForeignKey(orm['access.accessgroup'], null=False))
        ))
        db.create_unique('access_accessgroupmixin_access_groups', ['accessgroupmixin_id', 'accessgroup_id'])

        # Deleting field 'AccessGroup.public'
        db.delete_column('access_accessgroup', 'public')

        # Adding M2M table for field auto_share_groups on 'AccessGroup'
        db.create_table('access_accessgroup_auto_share_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_accessgroup', models.ForeignKey(orm['access.accessgroup'], null=False)),
            ('to_accessgroup', models.ForeignKey(orm['access.accessgroup'], null=False))
        ))
        db.create_unique('access_accessgroup_auto_share_groups', ['from_accessgroup_id', 'to_accessgroup_id'])


    def backwards(self, orm):
        
        # Deleting model 'AccessGroupMixin'
        db.delete_table('access_accessgroupmixin')

        # Removing M2M table for field access_groups on 'AccessGroupMixin'
        db.delete_table('access_accessgroupmixin_access_groups')

        # Adding field 'AccessGroup.public'
        db.add_column('access_accessgroup', 'public', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Removing M2M table for field auto_share_groups on 'AccessGroup'
        db.delete_table('access_accessgroup_auto_share_groups')


    models = {
        'access.accessgroup': {
            'Meta': {'ordering': "('name',)", 'object_name': 'AccessGroup'},
            'auto_share_groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'auto_share_groups_rel_+'", 'blank': 'True', 'to': "orm['access.AccessGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'supergroup': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'access.accessgroupmixin': {
            'Meta': {'object_name': 'AccessGroupMixin'},
            'access_groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['access.AccessGroup']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'access.invitation': {
            'Meta': {'ordering': "('lp_username',)", 'object_name': 'Invitation'},
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['access.AccessGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lp_username': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['access']
