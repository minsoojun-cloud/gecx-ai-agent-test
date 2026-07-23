<script defer
  src="https://www.gstatic.com/chat-messenger/sdk/prod/v1.16/chat-messenger.js">
</script>
<link rel="stylesheet" href="https://www.gstatic.com/chat-messenger/sdk/prod/v1.16/themes/chat-messenger-default.css">
<link rel="stylesheet" href="https://www.gstatic.com/chat-messenger/sdk/prod/v1.16/themes/chat-messenger-layout.css"></link>

<script>
    window.addEventListener("chat-messenger-loaded", () => {
      chatSdk.registerContext(
        chatSdk.prebuilts.ces.createContext({
          deploymentName: "projects/1064299839440/locations/us/apps/07a08655-1d08-44dc-a43b-ec06235393e1/deployments/52ccae7a-3ddc-4a40-bc3c-67821fde8b1b",
          tokenBroker: {
            enableTokenBroker: true,
            enableRecaptcha: false
          }
        }),
      );
    });
</script>
<!-- Update the url-allowlist attribute with a comma-separated list of origins allowed to render images -->
<chat-messenger
  url-allowlist="*"
>
  <chat-messenger-container
    chat-title="S-Minsoo-Test"
    chat-title-icon="https://gstatic.com/dialogflow-console/common/assets/ccai-favicons/conversational_agents.png"
    enable-file-upload
    enable-audio-input
  >
    <chat-reset-session-button
      slot="titlebar-actions"
      title-text="Start new chat"
    ></chat-reset-session-button>
    <chat-toggle-dialog-button
      slot="titlebar-actions"
      title-text-expanded="Collapse"
      title-text-collapsed="Expand"
    ></chat-toggle-dialog-button>
    <chat-messenger-close-button
      slot="titlebar-actions"
      title-text="Close"
    ></chat-messenger-close-button>
  </chat-messenger-container>
</chat-messenger>