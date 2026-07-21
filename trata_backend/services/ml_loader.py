# Patch pyparsing compatibility for older pySigma versions on Python 3.11+
import pyparsing
if not hasattr(pyparsing, "List"):
    from pyparsing import Forward
    # Fallback definition for the deprecated List helper
    pyparsing.List = Forward

import os
import yara
import networkx as nx
import joblib
import keras
from sigma.collection import SigmaCollection

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))

class MLModelLoader:
    def __init__(self):
        self.cnn_model = None
        self.supervised_engine = None
        self.yara_rules = None
        self.sigma_collection = None
        self.network_graph = None
        self.load_artifacts()

    def load_artifacts(self):
        # 1. Load CNN Model (.keras)
        cnn_path = os.path.join(MODELS_DIR, "CICIDS2018_CNN_Model.keras")
        if os.path.exists(cnn_path):
            try:
                self.cnn_model = keras.models.load_model(cnn_path)
            except Exception:
                pass

        # 2. Load Supervised Threat Engine (.joblib)
        joblib_path = os.path.join(MODELS_DIR, "supervised_threat_engine_uncompressed.joblib")
        if os.path.exists(joblib_path):
            try:
                self.supervised_engine = joblib.load(joblib_path)
            except Exception:
                pass

        # 3. Load pre-compiled YARA rules (core.yarc)
        yarc_path = os.path.join(MODELS_DIR, "core.yarc")
        if os.path.exists(yarc_path):
            try:
                self.yara_rules = yara.load(yarc_path)
            except Exception:
                pass

        # 4. Load official pySigma collection across directories and subfolders
        sigma_path = os.path.join(MODELS_DIR, "sigma_rules")
        if os.path.exists(sigma_path):
            try:
                self.sigma_collection = SigmaCollection.load_directory(sigma_path)
            except Exception:
                pass

        # 5. Load GML Network Graph (auth_massive_network_uncompressed.gml)
        gml_path = os.path.join(MODELS_DIR, "auth_massive_network_uncompressed.gml")
        if os.path.exists(gml_path):
            try:
                self.network_graph = nx.read_gml(gml_path)
            except Exception:
                pass

ml_manager = MLModelLoader()