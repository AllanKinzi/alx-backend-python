import unittest
from unittest.mock import patch, Mock
from parameterized import parameterized, parameterized_class
from client import GithubOrgClient
from fixtures import TEST_PAYLOAD


class TestGithubOrgClient(unittest.TestCase):
    """Test cases for GithubOrgClient class."""
    
    @parameterized.expand([
        ("google",),
        ("abc",),
    ])
    @patch('client.get_json')
    def test_org(self, org_name, mock_get_json):
        """Test that GithubOrgClient.org returns correct value."""
        test_payload = {"repos_url": f"https://api.github.com/orgs/{org_name}/repos"}
        mock_get_json.return_value = test_payload
        
        client = GithubOrgClient(org_name)
        result = client.org
        
        expected_url = f"https://api.github.com/orgs/{org_name}"
        mock_get_json.assert_called_once_with(expected_url)
        self.assertEqual(result, test_payload)

    def test_public_repos_url(self):
        """Test that _public_repos_url returns the expected URL from org payload."""
        test_payload = {
            "repos_url": "https://api.github.com/orgs/test-org/repos"
        }
        
        with patch.object(GithubOrgClient, 'org', new_callable=lambda: test_payload) as mock_org:
            client = GithubOrgClient("test-org")
            result = client._public_repos_url
            
            self.assertEqual(result, test_payload["repos_url"])

    @patch('client.get_json')
    def test_public_repos(self, mock_get_json):
        """Test that public_repos returns expected list of repo names."""
        test_repos_payload = [
            {"name": "repo1", "license": {"key": "mit"}},
            {"name": "repo2", "license": {"key": "apache-2.0"}},
            {"name": "repo3", "license": None}
        ]
        mock_get_json.return_value = test_repos_payload
        
        test_repos_url = "https://api.github.com/orgs/test-org/repos"
        
        with patch.object(GithubOrgClient, '_public_repos_url', 
                         new_callable=lambda: test_repos_url) as mock_repos_url:
            client = GithubOrgClient("test-org")
            result = client.public_repos()
            
            expected_repos = ["repo1", "repo2", "repo3"]
            self.assertEqual(result, expected_repos)
            
            # Verify mocked property was accessed
            mock_repos_url.__get__ = lambda *args: test_repos_url
            
            # Verify get_json was called once with the repos URL
            mock_get_json.assert_called_once_with(test_repos_url)

    @parameterized.expand([
        ({"license": {"key": "my_license"}}, "my_license", True),
        ({"license": {"key": "other_license"}}, "my_license", False),
    ])
    def test_has_license(self, repo, license_key, expected):
        """Test that has_license returns expected boolean value."""
        result = GithubOrgClient.has_license(repo, license_key)
        self.assertEqual(result, expected)


@parameterized_class(
    ("org_payload", "repos_payload", "expected_repos", "apache2_repos"),
    TEST_PAYLOAD
)
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration tests for GithubOrgClient class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up class method to start patcher for requests.get."""
        def side_effect(url):
            """Side effect function to return appropriate fixture based on URL."""
            mock_response = Mock()
            if url == GithubOrgClient.ORG_URL.format(org="google"):
                mock_response.json.return_value = cls.org_payload
            elif url == cls.org_payload["repos_url"]:
                mock_response.json.return_value = cls.repos_payload
            else:
                mock_response.json.return_value = {}
            return mock_response
        
        cls.get_patcher = patch('requests.get', side_effect=side_effect)
        cls.get_patcher.start()
    
    @classmethod
    def tearDownClass(cls):
        """Tear down class method to stop the patcher."""
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Test public_repos method returns expected results from fixtures."""
        client = GithubOrgClient("google")
        result = client.public_repos()
        self.assertEqual(result, self.expected_repos)

    def test_public_repos_with_license(self):
        """Test public_repos with license filter returns expected results."""
        client = GithubOrgClient("google")
        result = client.public_repos(license="apache-2.0")
        self.assertEqual(result, self.apache2_repos)


if __name__ == '__main__':
    unittest.main()