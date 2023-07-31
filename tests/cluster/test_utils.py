from django.test import TestCase

from tests.accounts.test_models import UserModelFactory
from tests.cluster.test_models import (
    ClusterChannelFactory,
    ClusterFactory,
    ClusterMembershipFactory,
    InternalClusterFactory,
)
from uia_backend.cluster.models import Cluster, ClusterMembership, InternalCluster
from uia_backend.cluster.utils import ClusterManager


class ClusterManagerTests(TestCase):
    def setUp(self) -> None:
        self.user = UserModelFactory.create()
        self.channel = ClusterChannelFactory.create()
        self.cluster_manager = ClusterManager(user=self.user)

    def test__create_default_cluster__cluster_already_exits__case_1(self):
        """
        Test behaviour of ClusterManager.__create_default_cluster when InternalCluster aleady exits and has Cluster.
        """

        # SETUP
        cluster_name = "Some Default Cluster"
        internal_cluster = InternalClusterFactory.create(name="Some Default Cluster")
        channel = ClusterChannelFactory.create(name="vashtor")
        ClusterFactory.create(
            internal_cluster=internal_cluster, title=cluster_name, channel=channel
        )

        # TEST
        self.cluster_manager._create_default_cluster(name=cluster_name, description="")

        # check that a new cluster was not created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

    def test__create_default_cluster__cluster_already_exits__case_2(self):
        """
        Test behaviour of ClusterManager.__create_default_cluster
        when InternalCluster aleady exits but has no Cluster.
        """

        # SETUP
        cluster_name = "Some Default Cluster"
        internal_cluster = InternalClusterFactory.create(name="Some Default Cluster")

        # TEST
        self.cluster_manager._create_default_cluster(name=cluster_name, description="")

        # check that a new InternalCluster was not created
        self.assertEqual(InternalCluster.objects.all().count(), 1)

        # check that Cluster was created
        internal_cluster.refresh_from_db()
        self.assertEqual(Cluster.objects.all().count(), 1)
        self.assertIsNotNone(internal_cluster.cluster)
        self.assertEqual(internal_cluster.cluster.title, cluster_name.capitalize())

    def test__create_default_cluster__does_not_exits(self):
        """Test behaviour of ClusterManager.__create_default_cluster when InternalCluster does not exits."""

        # SETUP
        cluster_name = "SomeDefaultCluster"
        # TEST
        self.cluster_manager._create_default_cluster(name=cluster_name, description="")

        # check that a new InternalCluster was created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        internal_cluster = InternalCluster.objects.first()
        cluster = Cluster.objects.first()

        self.assertEqual(internal_cluster.cluster, cluster)
        self.assertEqual(internal_cluster.name, cluster_name)
        self.assertEqual(cluster.title, cluster_name.capitalize())
        self.assertEqual(cluster.channel.name, "publicchannel:somedefaultcluster")

    def test__create_membership__case_1(self):
        """Test behaviour of ClusterManager._create_membership when user is not a member."""

        # SETUP
        internal_cluster = InternalClusterFactory.create(name="Some Default Cluster")
        channel = ClusterChannelFactory.create(name="ferus")
        cluster = ClusterFactory.create(
            internal_cluster=internal_cluster,
            title=internal_cluster.name,
            channel=channel,
        )

        # TEST
        self.cluster_manager._create_membership(cluster=cluster)

        cluster.refresh_from_db()
        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

    def test__create_membership__case_2(self):
        """Test behaviour of ClusterManager._create_membership when user is already a member."""

        # SETUP
        internal_cluster = InternalClusterFactory.create(name="Some Default Cluster")
        channel = ClusterChannelFactory.create(name="channel")
        cluster = ClusterFactory.create(
            internal_cluster=internal_cluster,
            title=internal_cluster.name,
            channel=channel,
        )
        membership = ClusterMembershipFactory.create(cluster=cluster, user=self.user)

        # TEST
        self.cluster_manager._create_membership(cluster=cluster)
        self.assertEqual(ClusterMembership.objects.all().count(), 1)
        self.assertIn(self.user, cluster.members.all())

        membership = ClusterMembership.objects.filter(
            cluster=cluster, user=self.user
        ).first()
        self.assertIsNotNone(membership)
        self.assertIsNone(membership.invitation)

    def test__add_user_to_global_cluster__case_1(self):
        """Test the behaviour of ClusterManager._add_user_to_global_cluster when global cluster already exists."""

        # SETUP
        global_cluster_name = "global"
        internal_cluster = InternalClusterFactory.create(name=global_cluster_name)
        channel = ClusterChannelFactory.create(name=global_cluster_name)
        cluster = ClusterFactory.create(
            internal_cluster=internal_cluster,
            title="Global",
            channel=channel,
        )

        # TEST
        self.cluster_manager._add_user_to_global_cluster()

        # check that a new cluster was not created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

        membership_object = self.cluster_manager.memberships_to_create[0]

        self.assertEqual(membership_object.cluster, cluster)
        self.assertEqual(membership_object.user, self.user)

    def test__add_user_to_global_cluster__case_2(self):
        """Test the behaviour of ClusterManager._add_user_to_global_cluster when global cluster does not exists."""

        # TEST
        self.cluster_manager._add_user_to_global_cluster()

        # check that a new cluster was created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        global_cluster = InternalCluster.objects.filter(
            name="global", description=""
        ).first()
        self.assertIsNotNone(global_cluster)
        self.assertIsNotNone(global_cluster.cluster)

        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

        membership_object = self.cluster_manager.memberships_to_create[0]

        self.assertEqual(membership_object.cluster, global_cluster.cluster)
        self.assertEqual(membership_object.user, self.user)

    def test__add_user_to_faculty_cluster__case_1(self):
        """Test the behaviour of ClusterManager._add_user_to_faculty_cluster when faculty cluster already exists."""

        # SETUP
        faculty_cluster_name = f"faculty of {self.user.faculty}"
        internal_cluster = InternalClusterFactory.create(name=faculty_cluster_name)
        channel = ClusterChannelFactory.create(name=faculty_cluster_name)
        cluster = ClusterFactory.create(
            internal_cluster=internal_cluster,
            title=faculty_cluster_name.capitalize(),
            channel=channel,
        )

        # TEST
        self.cluster_manager._add_user_to_faculty_cluster()

        # check that a new cluster was not created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

        membership_object = self.cluster_manager.memberships_to_create[0]

        self.assertEqual(membership_object.cluster, cluster)
        self.assertEqual(membership_object.user, self.user)

    def test__add_user_to_faculty_cluster__case_2(self):
        """Test the behaviour of ClusterManager._add_user_to_faculty_cluster when faculty cluster does not exist."""

        # TEST
        self.cluster_manager._add_user_to_faculty_cluster()

        # check that a new cluster was created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        faculty_cluster = InternalCluster.objects.filter(
            name=f"faculty of {self.user.faculty}", description=""
        ).first()
        self.assertIsNotNone(faculty_cluster)
        self.assertIsNotNone(faculty_cluster.cluster)

        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

        membership_object = self.cluster_manager.memberships_to_create[0]

        self.assertEqual(membership_object.cluster, faculty_cluster.cluster)
        self.assertEqual(membership_object.user, self.user)

    def test__add_user_to_department_cluster__case_1(self):
        """
        Test the behaviour of ClusterManager._add_user_to_department_cluster
        when department cluster already exists.
        """

        # SETUP
        department_cluster_name = f"{self.user.department} department"
        internal_cluster = InternalClusterFactory.create(name=department_cluster_name)
        channel = ClusterChannelFactory.create(name=department_cluster_name)
        cluster = ClusterFactory.create(
            internal_cluster=internal_cluster,
            title=department_cluster_name.capitalize(),
            channel=channel,
        )

        # TEST
        self.cluster_manager._add_user_to_department_cluster()

        # check that a new cluster was not created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

        membership_object = self.cluster_manager.memberships_to_create[0]

        self.assertEqual(membership_object.cluster, cluster)
        self.assertEqual(membership_object.user, self.user)

    def test__add_user_to_department_cluster__case_2(self):
        """
        Test the behaviour of ClusterManager._add_user_to_department_cluster
        when department cluster does not exist.
        """

        # TEST
        self.cluster_manager._add_user_to_department_cluster()

        # check that a new cluster was created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        department_cluster = InternalCluster.objects.filter(
            name=f"{self.user.department} department", description=""
        ).first()
        self.assertIsNotNone(department_cluster)
        self.assertIsNotNone(department_cluster.cluster)

        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

        membership_object = self.cluster_manager.memberships_to_create[0]

        self.assertEqual(membership_object.cluster, department_cluster.cluster)
        self.assertEqual(membership_object.user, self.user)

    def test__add_user_to_graduation_set_cluster__case_1(self):
        """
        Test the behaviour of ClusterManager._add_user_to_graduation_set_cluster
        when graduation set cluster already exists.
        """

        # SETUP
        yog_cluster_name = f"{self.user.year_of_graduation} set"
        internal_cluster = InternalClusterFactory.create(name=yog_cluster_name)
        channel = ClusterChannelFactory.create(name="gorgon")
        cluster = ClusterFactory.create(
            internal_cluster=internal_cluster,
            title=yog_cluster_name.capitalize(),
            channel=channel,
        )

        # TEST
        self.cluster_manager._add_user_to_graduation_set_cluster()

        # check that a new cluster was not created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

        membership_object = self.cluster_manager.memberships_to_create[0]

        self.assertEqual(membership_object.cluster, cluster)
        self.assertEqual(membership_object.user, self.user)

    def test__add_user_to_graduation_set_cluster__case_2(self):
        """
        Test the behaviour of ClusterManager._add_user_to_graduation_set_cluster
        when graduation set cluster does not exist.
        """

        # TEST
        self.cluster_manager._add_user_to_graduation_set_cluster()

        # check that a new cluster was created
        self.assertEqual(InternalCluster.objects.all().count(), 1)
        self.assertEqual(Cluster.objects.all().count(), 1)

        yog_cluster = InternalCluster.objects.filter(
            name=f"{self.user.year_of_graduation} set", description=""
        ).first()
        self.assertIsNotNone(yog_cluster)
        self.assertIsNotNone(yog_cluster.cluster)

        # TEST to ensure we dont save membership yet
        self.assertEqual(ClusterMembership.objects.all().count(), 0)
        self.assertEqual(len(self.cluster_manager.memberships_to_create), 1)

        membership_object = self.cluster_manager.memberships_to_create[0]

        self.assertEqual(membership_object.cluster, yog_cluster.cluster)
        self.assertEqual(membership_object.user, self.user)

    def test__add_user_to_defualt_clusters(self):
        """Test the behaviour of ClusterManager._add_user_to_defualt_clusters."""

        # TEST
        self.cluster_manager.add_user_to_defualt_clusters()

        self.assertEqual(InternalCluster.objects.all().count(), 4)
        self.assertEqual(Cluster.objects.all().count(), 4)
        self.assertEqual(ClusterMembership.objects.filter(user=self.user).count(), 4)

        global_cluster = InternalCluster.objects.filter(
            name="global", description=""
        ).first()
        self.assertIsNotNone(global_cluster)
        self.assertIsNotNone(global_cluster.cluster)
        self.assertTrue(
            ClusterMembership.objects.filter(
                user=self.user, cluster=global_cluster.cluster
            ).exists()
        )

        faculty_cluster = InternalCluster.objects.filter(
            name=f"faculty of {self.user.faculty}", description=""
        ).first()
        self.assertIsNotNone(faculty_cluster)
        self.assertIsNotNone(faculty_cluster.cluster)
        self.assertTrue(
            ClusterMembership.objects.filter(
                user=self.user, cluster=faculty_cluster.cluster
            ).exists()
        )

        department_cluster = InternalCluster.objects.filter(
            name=f"{self.user.department} department", description=""
        ).first()
        self.assertIsNotNone(department_cluster)
        self.assertIsNotNone(department_cluster.cluster)
        self.assertTrue(
            ClusterMembership.objects.filter(
                user=self.user, cluster=department_cluster.cluster
            ).exists()
        )

        yog_cluster = InternalCluster.objects.filter(
            name=f"{self.user.year_of_graduation} set", description=""
        ).first()
        self.assertIsNotNone(yog_cluster)
        self.assertIsNotNone(yog_cluster.cluster)
        self.assertTrue(
            ClusterMembership.objects.filter(
                user=self.user, cluster=yog_cluster.cluster
            ).exists()
        )
