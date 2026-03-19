#!/usr/bin/env python3
"""
Flutter feature scaffolding script for flutter-app-builder skill.

Usage:
  python generate_feature.py --feature item_list --tier 1 --output lib/
  python generate_feature.py --feature item_list --tier 2 --output lib/
  python generate_feature.py --feature item_list --tier 2 --dry-run
"""

import argparse
import os
import re
import sys


def to_pascal_case(snake_str: str) -> str:
    return ''.join(word.capitalize() for word in snake_str.split('_'))


def to_snake_case(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def write_file(path: str, content: str, dry_run: bool) -> None:
    if dry_run:
        print(f"[DRY RUN] Would create: {path}")
        print(content)
        print("---")
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        print(f"Created: {path}")


# ─── Tier 1 Templates ─────────────────────────────────────────────────────────

def tier1_state(feature: str, pascal: str) -> str:
    return f"""sealed class {pascal}State {{}}

class {pascal}Initial extends {pascal}State {{}}

class {pascal}Loading extends {pascal}State {{}}

class {pascal}Success extends {pascal}State {{
  final List<dynamic> items;
  {pascal}Success(this.items);
}}

class {pascal}Error extends {pascal}State {{
  final String message;
  {pascal}Error(this.message);
}}
"""


def tier1_cubit(feature: str, pascal: str) -> str:
    return f"""import 'package:flutter_bloc/flutter_bloc.dart';

import '{feature}_state.dart';

class {pascal}Cubit extends Cubit<{pascal}State> {{
  {pascal}Cubit() : super({pascal}Initial());

  Future<void> load() async {{
    emit({pascal}Loading());
    try {{
      // TODO: inject repository and fetch data
      final items = <dynamic>[];
      emit({pascal}Success(items));
    }} catch (e) {{
      emit({pascal}Error(e.toString()));
    }}
  }}
}}
"""


def tier1_screen(feature: str, pascal: str) -> str:
    return f"""import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '{feature}_cubit.dart';
import '{feature}_state.dart';

class {pascal}Screen extends StatelessWidget {{
  const {pascal}Screen({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return BlocBuilder<{pascal}Cubit, {pascal}State>(
      builder: (context, state) => switch (state) {{
        {pascal}Initial() || {pascal}Loading() => const Center(child: CircularProgressIndicator()),
        {pascal}Success(:final items) => ListView.builder(
          itemCount: items.length,
          itemBuilder: (_, i) => ListTile(title: Text(items[i].toString())),
        ),
        {pascal}Error(:final message) => Center(child: Text(message)),
      }},
    );
  }}
}}
"""


def tier1_page(feature: str, pascal: str) -> str:
    return f"""import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '{feature}_cubit.dart';
import '{feature}_screen.dart';

class {pascal}Page extends StatelessWidget {{
  const {pascal}Page({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return BlocProvider(
      create: (_) => {pascal}Cubit()..load(),
      child: const {pascal}Screen(),
    );
  }}
}}
"""


# ─── Tier 2 Templates ─────────────────────────────────────────────────────────

def tier2_entity(feature: str, pascal: str) -> str:
    return f"""import 'package:freezed_annotation/freezed_annotation.dart';

part '{feature}_item.freezed.dart';

@freezed
class {pascal}Item with _${pascal}Item {{
  const factory {pascal}Item({{
    required String id,
    required String name,
    required DateTime createdAt,
  }}) = _{pascal}Item;
}}
"""


def tier2_repository(feature: str, pascal: str) -> str:
    return f"""import '../entities/{feature}_item.dart';

abstract interface class {pascal}Repository {{
  Stream<List<{pascal}Item>> watch{pascal}s();
  Future<List<{pascal}Item>> get{pascal}s();
  Future<void> save{pascal}({pascal}Item item);
  Future<void> delete{pascal}(String id);
  Future<void> sync();
}}
"""


def tier2_repository_impl(feature: str, pascal: str) -> str:
    return f"""import 'package:injectable/injectable.dart';

import '../../domain/entities/{feature}_item.dart';
import '../../domain/repositories/{feature}_repository.dart';

@LazySingleton(as: {pascal}Repository)
class {pascal}RepositoryImpl implements {pascal}Repository {{
  {pascal}RepositoryImpl();
  // TODO: inject LocalDataSource and RemoteDataSource

  @override
  Stream<List<{pascal}Item>> watch{pascal}s() => throw UnimplementedError();

  @override
  Future<List<{pascal}Item>> get{pascal}s() async => throw UnimplementedError();

  @override
  Future<void> save{pascal}({pascal}Item item) async => throw UnimplementedError();

  @override
  Future<void> delete{pascal}(String id) async => throw UnimplementedError();

  @override
  Future<void> sync() async => throw UnimplementedError();
}}
"""


def tier2_usecase(feature: str, pascal: str) -> str:
    return f"""import 'package:injectable/injectable.dart';

import '../entities/{feature}_item.dart';
import '../repositories/{feature}_repository.dart';

@injectable
class Get{pascal}sUseCase {{
  Get{pascal}sUseCase(this._repository);
  final {pascal}Repository _repository;

  Future<List<{pascal}Item>> call() => _repository.get{pascal}s();
}}
"""


def tier2_state(feature: str, pascal: str) -> str:
    return f"""import 'package:freezed_annotation/freezed_annotation.dart';

import '../../domain/entities/{feature}_item.dart';

part '{feature}_state.freezed.dart';

@freezed
sealed class {pascal}State with _${pascal}State {{
  const factory {pascal}State.loading() = _Loading;
  const factory {pascal}State.success(List<{pascal}Item> items) = _Success;
  const factory {pascal}State.error(String message) = _Error;
}}
"""


def tier2_event(feature: str, pascal: str) -> str:
    return f"""import 'package:freezed_annotation/freezed_annotation.dart';

part '{feature}_event.freezed.dart';

@freezed
sealed class {pascal}Event with _${pascal}Event {{
  const factory {pascal}Event.started() = _Started;
  const factory {pascal}Event.refreshed() = _Refreshed;
  const factory {pascal}Event.deleted(String id) = _Deleted;
}}
"""


def tier2_bloc(feature: str, pascal: str) -> str:
    return f"""import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:injectable/injectable.dart';

import '../../domain/usecases/get_{feature}s_usecase.dart';
import '{feature}_event.dart';
import '{feature}_state.dart';

@injectable
class {pascal}Bloc extends Bloc<{pascal}Event, {pascal}State> {{
  {pascal}Bloc(this._get{pascal}s) : super(const {pascal}State.loading()) {{
    on<_Started>(_onStarted);
    on<_Refreshed>(_onStarted);
    on<_Deleted>(_onDeleted);
  }}

  final Get{pascal}sUseCase _get{pascal}s;

  Future<void> _onStarted(_Started event, Emitter<{pascal}State> emit) async {{
    emit(const {pascal}State.loading());
    try {{
      final items = await _get{pascal}s();
      emit({pascal}State.success(items));
    }} catch (e) {{
      emit({pascal}State.error(e.toString()));
    }}
  }}

  Future<void> _onDeleted(_Deleted event, Emitter<{pascal}State> emit) async {{
    // TODO: implement delete
  }}
}}
"""


def tier2_page(feature: str, pascal: str) -> str:
    return f"""import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get_it/get_it.dart';

import 'bloc/{feature}_bloc.dart';
import 'bloc/{feature}_event.dart';
import '{feature}_screen.dart';

class {pascal}Page extends StatelessWidget {{
  const {pascal}Page({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return BlocProvider(
      create: (_) => GetIt.I<{pascal}Bloc>()..add(const {pascal}Event.started()),
      child: const {pascal}Screen(),
    );
  }}
}}
"""


def tier2_screen(feature: str, pascal: str) -> str:
    return f"""import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import 'bloc/{feature}_bloc.dart';
import 'bloc/{feature}_state.dart';

class {pascal}Screen extends StatelessWidget {{
  const {pascal}Screen({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return BlocBuilder<{pascal}Bloc, {pascal}State>(
      builder: (context, state) => state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        success: (items) => ListView.builder(
          itemCount: items.length,
          itemBuilder: (_, i) => ListTile(title: Text(items[i].name)),
        ),
        error: (message) => Center(child: Text(message)),
      ),
    );
  }}
}}
"""


# ─── Main ──────────────────────────────────────────────────────────────────────

def generate_tier1(feature: str, pascal: str, output: str, dry_run: bool) -> None:
    base = os.path.join(output, 'features', feature)
    write_file(os.path.join(base, f'{feature}_state.dart'), tier1_state(feature, pascal), dry_run)
    write_file(os.path.join(base, f'{feature}_cubit.dart'), tier1_cubit(feature, pascal), dry_run)
    write_file(os.path.join(base, f'{feature}_screen.dart'), tier1_screen(feature, pascal), dry_run)
    write_file(os.path.join(base, f'{feature}_page.dart'), tier1_page(feature, pascal), dry_run)


def generate_tier2(feature: str, pascal: str, output: str, dry_run: bool) -> None:
    base = os.path.join(output, 'features', feature)

    write_file(os.path.join(base, 'domain', 'entities', f'{feature}_item.dart'), tier2_entity(feature, pascal), dry_run)
    write_file(os.path.join(base, 'domain', 'repositories', f'{feature}_repository.dart'), tier2_repository(feature, pascal), dry_run)
    write_file(os.path.join(base, 'domain', 'usecases', f'get_{feature}s_usecase.dart'), tier2_usecase(feature, pascal), dry_run)
    write_file(os.path.join(base, 'data', 'repositories', f'{feature}_repository_impl.dart'), tier2_repository_impl(feature, pascal), dry_run)
    write_file(os.path.join(base, 'presentation', 'bloc', f'{feature}_state.dart'), tier2_state(feature, pascal), dry_run)
    write_file(os.path.join(base, 'presentation', 'bloc', f'{feature}_event.dart'), tier2_event(feature, pascal), dry_run)
    write_file(os.path.join(base, 'presentation', 'bloc', f'{feature}_bloc.dart'), tier2_bloc(feature, pascal), dry_run)
    write_file(os.path.join(base, 'presentation', f'{feature}_page.dart'), tier2_page(feature, pascal), dry_run)
    write_file(os.path.join(base, 'presentation', f'{feature}_screen.dart'), tier2_screen(feature, pascal), dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Generate Flutter feature scaffold for flutter-app-builder skill'
    )
    parser.add_argument('--feature', required=True, help='Feature name in snake_case (e.g. item_list)')
    parser.add_argument('--tier', required=True, choices=['1', '2'], help='Architecture tier (1=Simple, 2=Production)')
    parser.add_argument('--output', default='lib', help='Output directory (default: lib/)')
    parser.add_argument('--dry-run', action='store_true', help='Print files without writing')

    args = parser.parse_args()

    feature = to_snake_case(args.feature)
    pascal = to_pascal_case(feature)
    tier = int(args.tier)
    output = args.output
    dry_run = args.dry_run

    print(f"Generating Tier {tier} feature '{pascal}' in {output}/features/{feature}/")

    if tier == 1:
        generate_tier1(feature, pascal, output, dry_run)
    else:
        generate_tier2(feature, pascal, output, dry_run)

    if not dry_run and tier == 2:
        print("\nNext step: run code generation")
        print("  dart run build_runner build --delete-conflicting-outputs")


if __name__ == '__main__':
    main()
