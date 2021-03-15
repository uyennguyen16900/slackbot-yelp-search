package main

import (
	"log"

	"github.com/slack-go/slack"
)

func main() {
	OAUTH_TOKEN := "xoxb-1303899646098-1846760895863-7I0u8xonCO69oxKOTlVC7rzJ"
	CHANNEL_ID := "C01R8CRBX1B"

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
