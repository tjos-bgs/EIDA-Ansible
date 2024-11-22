// Switch to wfrepo database
db = db.getSiblingDB("wfrepo");

db.createUser({
    user: "wfcatalogwrite",
    pwd: "<redacted>",
    roles: [{
        role: "readWrite",
        db: "wfrepo"
    }]
});

db.createUser({
    user: "wfcatalogread",
    pwd: "<redacted>",
    roles: [{
        role: "read",
        db: "wfrepo"
    }]
});

// Create index
db.availability.createIndex({ net: 1, sta: 1, loc: 1, cha: 1, ts: 1, te: 1 });
