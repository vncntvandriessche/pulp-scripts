from pulp.bindings.search import SearchAPI
from pulp.bindings.base import PulpAPI

from collections import defaultdict
import datetime

# from pulp.bindings.search import SearchAPI

class Package(object):
    
    def __init__(self, search_result):
        self.name = search_result['metadata']['name']
        self.filename = search_result['metadata']['filename']
        
        self.unit_id = search_result['unit_id']
        
        self.created = datetime.datetime.strptime(search_result['created'], "%Y-%m-%dT%H:%M:%SZ")

    def is_more_recent(self, second):
        """
        Checks if current package is more recent 
        compared to a second package
        """
        return self.created > second.created


class PackagesPerRepositoryAPI(SearchAPI):
    """
    Extends default SearchAPI to allow searching for packages.

    The binding's repository modules seems to include a more
    generic approach to this, we can omit this class and use
    the pulp version instead.
    """

    def __init__(self, pulp_connection, repository=None):
        self.PATH = "/v2/repositories/%s/search/units/" % repository
        super(PackagesPerRepositoryAPI, self).__init__(pulp_connection)

class ContentManipulationAPI(PulpAPI):
    """
    Handles the manipulation of content, like operations performed on units
    """
    
    def __init__(self, pulp_connection, repository=None):
        """
        @type:  pulp_connection: pulp.bindings.server.PulpConnection
        """
        self.base_path = "/pulp/api/v2/repositories/%s/actions/" % repository
        super(ContentManipulationAPI, self).__init__( pulp_connection )

    def unassociate(self, unit_id):
        path = "%sunassociate/" % self.base_path
        criteria = {"criteria": {"type_ids":["rpm"],"filters":{"unit":{"unit_id": {"$in":[unit_id]}}}}}
        return self.server.POST(path, criteria)

class PackageVersionManager(object):
    """
    Handles the version control of a list of ``Package`` objects.
    """

    DETAIN_AMOUNT = 3
    """Specifies the maximum amount of packages that should be kept on the server"""

    def __init__(self, search_results):
        """
        Takes search results from a ``PulpAPI`` and transforms 
        them into ``Package`` objects.
        """
        # list representation of packages
        packages = [Package(p) for p in search_results]
        
        # dictionary representation of packages based on name
        # key = package name
        # value = package object
        self._packages = defaultdict(list)
        for pkg in packages:
            self._packages[pkg.name].append(pkg)


    # -- retrieval

    def get_packages(self):
        """
        Returns all ``Package`` objects contained in this manager
        """
        return self._packages

    def get_packages_to_purge(self):
        """
        Returns a list of ``Package`` objects that have  newer versions already installed.

        By default, it will use ``DETAIN_AMOUNT`` to keep that many 
        versions out of the purge list on the system
        """
        purge_list = []
        # iterate over all installed package names:
        for pkg_name, packages in self.get_packages().iteritems():
            # sort packages based on creation date (earliest to latest)
            sorted_packages = sorted(packages, lambda x,y: cmp(x.created, y.created))
            # return everything except the last ``DETAIN_AMOUNT`` of packages
            packages_to_purge = sorted_packages[:-self.DETAIN_AMOUNT]
            # add to purge list
            purge_list += packages_to_purge

        return purge_list

    # -- printing

    def print_all_packages(self):
        """
        Prints out all ``Package`` objects contained in this manager.
        """
        print "---------------------------------------------------------"
        print "Installed Packages"
        print "---------------------------------------------------------"
        for pkg_name, pkgs in self.get_packages().iteritems():
            print "* %s: %s" % (pkg_name, ", ".join([p.filename for p in pkgs]))
        print

    def print_packages_to_purge(self):
        """
        Prints out all ``Package`` objects contained in this manager that
        are candidates for purging.
        """
        print "---------------------------------------------------------"
        print "Purge Candidate Packages"
        print "---------------------------------------------------------"
        for pkg in self.get_packages_to_purge():
            print "* %s: %s (unit_id=%s)" % (pkg.name, pkg.filename, pkg.unit_id)
        print

if __name__ == '__main__':
    
    test_installed_packages = [
        {
            'metadata' : {
                'name': 'pkg_one',
                'filename': 'pkg_one-1.rpm'
            },
            'unit_id': 1,
            'created': datetime.datetime(2013,01,01).strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        {
            'metadata' : {
                'name': 'pkg_one',
                'filename': 'pkg_one-2.rpm'
            },
            'unit_id': 2,
            'created': datetime.datetime(2013,01,02).strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        {
            'metadata' : {
                'name': 'pkg_one',
                'filename': 'pkg_one-3.rpm'
            },
            'unit_id': 3,
            'created': datetime.datetime(2013,01,03).strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        {
            'metadata' : {
                'name': 'pkg_one',
                'filename': 'pkg_one-4.rpm'
            },
            'unit_id': 4,
            'created': datetime.datetime(2013,01,04).strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        {
            'metadata' : {
                'name': 'pkg_two',
                'filename': 'pkg_two-1.rpm'
            },
            'unit_id': 5,
            'created': datetime.datetime(2013,01,04).strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        {
            'metadata' : {
                'name': 'pkg_two',
                'filename': 'pkg_two-2.rpm'
            },
            'unit_id': 6,
            'created': datetime.datetime(2013,01,05).strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        {
            'metadata' : {
                'name': 'pkg_two',
                'filename': 'pkg_two-3.rpm'
            },
            'unit_id': 7,
            'created': datetime.datetime(2013,01,06).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    ]

    version_mgr = PackageVersionManager( test_installed_packages )
    version_mgr.print_all_packages()
    version_mgr.print_packages_to_purge()
