from django.core.paginator import Paginator

from djapian.tests.utils import BaseTestCase, Entry, Person
from djapian.utils.commiter import Commiter

class CommiterTest(BaseTestCase):
    num_entries = 30
    per_page = 10
    num_pages = num_entries / per_page

    def test_concrete_commiter_page(self):
        def _begin():
            return 'begin'
        def _commit():
            return 'commit'
        def _rollback():
            return 'rollback'

        commiter = Commiter.create(False)(
            _begin,
            _commit,
            _rollback
        )

        self.assertEqual(commiter.begin_object(), None)
        self.assertEqual(commiter.commit_object(), None)
        self.assertEqual(commiter.cancel_object(), None)
        self.assertEqual(commiter.begin_page(), 'begin')
        self.assertEqual(commiter.commit_page(), 'commit')
        self.assertEqual(commiter.cancel_page(), 'rollback')

    def test_concrete_commiter_object(self):
        def _begin():
            return 'begin'
        def _commit():
            return 'commit'
        def _rollback():
            return 'rollback'

        commiter = Commiter.create(True)(
            _begin,
            _commit,
            _rollback
        )

        self.assertEqual(commiter.begin_page(), None)
        self.assertEqual(commiter.commit_page(), None)
        self.assertEqual(commiter.cancel_page(), None)
        self.assertEqual(commiter.begin_object(), 'begin')
        self.assertEqual(commiter.commit_object(), 'commit')
        self.assertEqual(commiter.cancel_object(), 'rollback')

    def test_bulk_delete(self):
        p = Person.objects.create(name="Alex")
        for i in range(self.num_entries):
            Entry.objects.create(
                author=p,
                title="Entry with number %s" % i,
                text="foobar " * i
            )
        Entry.indexer.update()

        result = Entry.indexer.search("title:number")

        database = Entry.indexer._db.open(write=True)

        commiter = Commiter.create(False)(
            database.begin_transaction,
            database.commit_transaction,
            database.cancel_transaction
        )

        result_count = result.count()
        paginator = Paginator(result, self.per_page)

        self.assertEqual(paginator.num_pages, self.num_pages)

        page = paginator.page(2)

        commiter.begin_page()
        try:
            for obj in page.object_list:
                commiter.begin_object()
                try:
                    Entry.indexer.delete(obj.pk, database=database)
                    commiter.commit_object()
                except Exception:
                    commiter.cancel_object()
                    raise

            commiter.commit_page()
        except Exception:
            commiter.cancel_page()
            raise

        # database.commit() if hasattr(database, 'commit') else database.flush()
        self.assertEqual(Entry.indexer.search("title:number").count(),
                         result_count - self.per_page)
