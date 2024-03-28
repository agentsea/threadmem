import React from "react";
import { Card, CardBody, Typography } from "@material-tailwind/react";

export default function RoleThread({ msgs }) {
  return (
    <div className="flex flex-col gap-4 p-4">
      {msgs.map((msg, index) => (
        <Card key={index} className="max-w-sm">
          <CardBody className="flex flex-col gap-2">
            <Typography variant="h6" color="blue-gray" className="font-bold">
              {msg.role}
            </Typography>
            <Typography variant="paragraph" color="blue-gray">
              {msg.text}
            </Typography>
            {msg.images &&
              msg.images.map((image, index) => (
                <img
                  key={index}
                  src={image}
                  alt={`attachment-${index}`}
                  className="max-w-full h-auto rounded-lg"
                />
              ))}
            <Typography variant="small" color="gray">
              {new Date(msg.created).toLocaleString()}
            </Typography>
          </CardBody>
        </Card>
      ))}
    </div>
  );
}
