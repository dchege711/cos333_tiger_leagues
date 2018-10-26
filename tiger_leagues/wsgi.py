import os

import tiger_leagues

port = int(os.environ.get('PORT', 5000))
app = tiger_leagues.create_app()
