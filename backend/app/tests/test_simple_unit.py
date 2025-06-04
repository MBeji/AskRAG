"""
Test simple pour vérifier le setup de test
"""

import pytest


def test_simple():
    """Test simple pour vérifier que pytest fonctionne"""
    assert True


def test_math():
    """Test mathématique simple"""
    assert 1 + 1 == 2


class TestBasic:
    """Classe de test basique"""
    
    def test_basic_assertion(self):
        """Test d'assertion basique"""
        assert "hello" == "hello"
    
    def test_list_operations(self):
        """Test d'opérations sur les listes"""
        test_list = [1, 2, 3]
        assert len(test_list) == 3
        assert 2 in test_list
