db = db.getSiblingDB('phishing_feedback');

db.createUser({
  user: 'admin',
  pwd: 'password',
  roles: [
    { role: 'readWrite', db: 'phishing_feedback' }
  ]
});

db.createCollection('user_feedback');