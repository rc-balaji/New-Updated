import json

from Bins import Bin


class BinConstants:
    def __init__(self, rack_id, bins_config, bin_manager, server_ip, kt_id, sta):
        self.bins = [
            Bin(
                bin_cfg,
                idx,
                rack_id,
                bin_manager=bin_manager,
                server_ip=server_ip,
                kt_id=kt_id,
                sta=sta,
            )
            for idx, bin_cfg in enumerate(bins_config)
        ]
