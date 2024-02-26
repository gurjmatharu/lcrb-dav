db.createUser({
    user: "davcontrolleruser",
    pwd: "davcontrollerpass",
    roles: [
      {
        role: "readWrite",
        db: "davcontroller",
      },
    ],
  });
  