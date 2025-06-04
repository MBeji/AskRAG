"""
Runner pour les tests de performance AskRAG
Étape 16.4.5 - Exécution automatique des tests de performance
"""

import asyncio
import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Configuration du logging pour les tests
import logging
logging.basicConfig(
    level=logging.WARNING,  # Réduire le bruit pour les tests de performance
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def run_performance_tests():
    """Lance tous les tests de performance"""
    print("🚀 DÉMARRAGE DES TESTS DE PERFORMANCE ASKRAG")
    print("=" * 60)
    
    try:
        # Importer et exécuter les tests
        from app.tests.test_rag_performance import run_all_performance_tests
        
        success = await run_all_performance_tests()
        
        if success:
            print("\n🎉 SUCCÈS - Tous les tests de performance sont passés!")
            return 0
        else:
            print("\n❌ ÉCHEC - Certains tests de performance ont échoué!")
            return 1
            
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Vérifiez que tous les modules sont disponibles")
        return 1
    except Exception as e:
        print(f"💥 Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Point d'entrée principal"""
    print("RUNNER DES TESTS DE PERFORMANCE")
    print("Étape 16.4.5 - Validation des optimisations")
    print()
    
    # Vérifier l'environnement
    if not os.path.exists("app"):
        print("❌ Erreur: Exécutez ce script depuis le répertoire backend")
        return 1
    
    # Lancer les tests
    try:
        result = asyncio.run(run_performance_tests())
        return result
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrompus par l'utilisateur")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
