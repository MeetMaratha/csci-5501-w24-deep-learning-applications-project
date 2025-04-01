from typing import Tuple

import torch
import torch.nn as nn
from decoder import Decoder
from encoder import Encoder


class SequenceToSequence(nn.Module):

    def __init__(
        self,
        encoder: Encoder,
        decoder: Decoder,
        device: torch.device,
    ) -> None:

        super(SequenceToSequence, self).__init__()
        self.encoder: Encoder = encoder
        self.decoder: decoder = decoder
        self.device: torch.device = device
        return None

    def forward(
        self,
        tokenized_source_sentence: torch.Tensor,
        tokenized_target_sentence: torch.Tensor,
        teacher_forcing: bool = True,
    ) -> torch.Tensor:
        """
        tokenized_source_sentence (torch.Tensor): tokenized input source sentence that needs to be translated. (batch_size, source_sentence_tokenized_length)
        tokenized_target_sentence (torch.Tensor): tokenized target source sentence that needs to be predicted. (batch_size, target_sentence_tokenized_length)
        teacher_forcing (bool): Whether we are forcing the original text instead of predicted text to the decoder.
        """

        batch_size: int = tokenized_source_sentence.shape[0]
        target_sentence_length: int = tokenized_target_sentence.shape[1]
        target_sentence_vocab_length: int = self.decoder.fc_out.out_features

        # A tensor to store decoder outputs.
        # Output: (batch_size, target_sentence_length, target_language_vocab_length)
        output: torch.Tensor = torch.zeros(
            size=(batch_size, target_sentence_length, target_sentence_vocab_length),
            device=self.device,
        )

        # Encode the source sentence
        # Hidden: (num_layers, batch_size, hidden_dim)
        # Cell: (num_layers, batch_size, hidden_dim)
        hidden_layer: torch.Tensor
        cell_layer: torch.Tensor
        hidden_layer, cell_layer = self.encoder(tokenized_source_sentence)

        # First input to the decoder is the <Start Of Sequence> token,
        # we get it from the tokenized_target_sentence first token.
        target_input: torch.Tensor = tokenized_target_sentence[:, 0].reshape(
            shape=(batch_size, 1)
        )

        for prediction_index in range(1, target_sentence_length):

            # Pass the latest target_input through the decoder with
            # encoded hidden and cell layers
            # Output Dim: (batch_size, 1, hidden_dim)
            # Hidden Dim: (num_layers, batch_size, hidden_dim)
            # Cell Dim: (num_layers, batch_size, hidden_dim)
            decoder_output: torch.Tensor

            decoder_output, hidden_layer, cell_layer = self.decoder(
                target_input, hidden_layer, cell_layer
            )

            # Set the output generated by decoder to the cummulative
            # output
            output[:, prediction_index] = decoder_output

            target_input = (
                tokenized_target_sentence[:, prediction_index].reshape(
                    shape=(batch_size, 1)
                )
                if teacher_forcing
                else decoder_output.argmax(1)
            )

        return output


if __name__ == "__main__":

    batch_size: int = 4
    embedding_dim: int = 1024
    num_layers: int = 2
    hidden_dim: int = 1024
    vocab_size: int = 2048
    input_sentnece_dim: int = 512
    encoder: Encoder = Encoder(
        vocab_size=vocab_size,
        embedding_dim=embedding_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
    )

    decoder: Decoder = Decoder(
        output_dim=vocab_size,
        embedding_dim=embedding_dim,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
    )

    seq_to_seq: SequenceToSequence = SequenceToSequence(
        encoder=encoder,
        decoder=decoder,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
    )

    tokenized_source_input: torch.Tensor = torch.randint(
        low=0, high=vocab_size, size=(batch_size, input_sentnece_dim)
    )

    tokenized_target_input: torch.Tensor = torch.randint(
        low=0, high=vocab_size, size=(batch_size, input_sentnece_dim)
    )

    output: torch.Tensor = seq_to_seq(
        tokenized_source_sentence=tokenized_source_input,
        tokenized_target_sentence=tokenized_target_input,
        teacher_forcing=True,
    )

    print("Source Input Shape: ", tokenized_source_input.shape)
    print("Target Input Shape: ", tokenized_target_input.shape)
    print("Output Shape: ", output.shape)
    print("Device used: ", torch.device("cuda" if torch.cuda.is_available() else "cpu"))
