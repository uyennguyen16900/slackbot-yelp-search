package main

import (
	"log"

	"github.com/slack-go/slack"
)

func main() {

	api := slack.New(OAUTH_TOKEN)
	attachment := slack.Attachment{
		Pretext: "Pretext",
		Text:    "Hello from GolangDocs",
	}

	channelID, timestamp, err := api.PostMessage(
		CHANNEL_ID,
		slack.MsgOptionText("This is the main message", false),
		slack.MsgOptionAttachments(attachment),
		slack.MsgOptionAsUser(true),
	)

	if err != nil {
		log.Fatalf("%s\n", err)
	}

	log.Printf("Message successfullt sent to Channel %s at %s\n", channelID, timestamp)
}
