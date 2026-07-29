"""
Bu uygulamanin modelleri, orijinal ofis-gorev-takibi (Node.js) projesinin
KENDI SQLite dosyasina isaret eder. Discord bot ve cron o dosyayi hala
kendi surecinde okuyup yaziyor; Portal artik ayni dosyaya Django ORM
uzerinden dogrudan okuyup yaziyor.

`managed = False` (modellerde) + bu router'in `allow_migrate` -> False
donmesi sayesinde Django bu tablolar icin HICBIR migration uretmez/uygulamaz
- semanin sahibi hep orijinal Node projesidir (database/schema.js).
"""


class OfficeBotRouter:
    route_app_labels = {"office_bot"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "office_bot"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "office_bot"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in self.route_app_labels or obj2._meta.app_label in self.route_app_labels:
            return obj1._meta.app_label == obj2._meta.app_label
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return False
        return None
