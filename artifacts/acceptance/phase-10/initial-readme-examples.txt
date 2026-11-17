Traceback (most recent call last):
  File "/Users/tinaluo/Documents/nexus实习/downloading-usda-data/scripts/handover_examples.py", line 107, in <module>
    main()
    ~~~~^^
  File "/Users/tinaluo/Documents/nexus实习/downloading-usda-data/scripts/handover_examples.py", line 81, in main
    frame = download_dataset(dataset, data_dir=data, **options)
  File "/Users/tinaluo/Documents/nexus实习/downloading-usda-data/artifacts/acceptance/phase-10/clean-venv/lib/python3.13/site-packages/usda_data/api.py", line 52, in download_dataset
    return download_wasde(data_dir=data_dir,**validated_dataset_options)
  File "/Users/tinaluo/Documents/nexus实习/downloading-usda-data/artifacts/acceptance/phase-10/clean-venv/lib/python3.13/site-packages/usda_data/api.py", line 14, in download_wasde
    frames=list(iter_wasde(start,end,data_dir=data_dir,refresh=refresh))
  File "/Users/tinaluo/Documents/nexus实习/downloading-usda-data/artifacts/acceptance/phase-10/clean-venv/lib/python3.13/site-packages/usda_data/api.py", line 19, in iter_wasde
    yield from iter_download(start,end,data_dir=data_dir,refresh=refresh)
  File "/Users/tinaluo/Documents/nexus实习/downloading-usda-data/artifacts/acceptance/phase-10/clean-venv/lib/python3.13/site-packages/usda_data/sources/wasde.py", line 301, in iter_download
    manifest=store.publish('wasde',release.isoformat(),frame,SCHEMA,artifact_ids,parser_version=PARSER_VERSION,configuration={'source':'official long-form CSV','layout':COLUMNS})
  File "/Users/tinaluo/Documents/nexus实习/downloading-usda-data/artifacts/acceptance/phase-10/clean-venv/lib/python3.13/site-packages/usda_data/storage.py", line 98, in publish
    raise ValidationError("Nondeterministic snapshot output; increment parser/config version")
usda_data.errors.ValidationError: Nondeterministic snapshot output; increment parser/config version
