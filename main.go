package main

import (
	"log"
	"os"

	"github.com/joho/godotenv"
	"github.com/slack-go/slack"
)

func getEnvVars() {
	err := godotenv.Load("credentials.env")
	if err != nil {
		log.Fatal("Error loading .env file")
	}
}

func main() {
	getEnvVars()
	oauthToken := os.Getenv("OAUTH_TOKEN")
	channelID := os.Getenv("CHANNEL_ID")

	api := slack.New(oauthToken)
	attachment := slack.Attachment{
		Pretext: "Pretext",
		Text:    "Hello from GolangDocs",
	}

	channelID, timestamp, err := api.PostMessage(
		channelID,
		slack.MsgOptionText("This is the main message", false),
		slack.MsgOptionAttachments(attachment),
		slack.MsgOptionAsUser(true),
	)

	if err != nil {
		log.Fatalf("%s\n", err)
	}

	log.Printf("Message successfullt sent to Channel %s at %s\n", channelID, timestamp)
}
