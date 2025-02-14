import click
from core.photo_dumper import PhotoDumper

@click.command()
@click.argument('album_path', type=click.Path(exists=True))
@click.argument('categories_file', type=click.Path(exists=True), default='defaults/photodump_list.txt')
@click.option('--batch-size', default=1, help='Number of images to process in each batch')
@click.option('--pre-filter', default=100, help='Number of photos to pre-filter per category')
@click.option('--keep-top-k', default=1, help='Number of top photos to keep per category')
@click.option('--output-dir', default='output', help='Directory to save output files')
@click.option('--aesthetic-weight', default=0.6, help='Weight given to aesthetic score vs CLIP score')
def main(album_path, categories_file, batch_size, pre_filter, keep_top_k, output_dir, aesthetic_weight):
    """Generate AI photo dump by categorizing photos and selecting the best ones.
    
    ALBUM_PATH: Path to folder containing photos
    CATEGORIES_FILE: Path to text file containing numbered categories
    """
    click.echo("Categorizing photos...")
    photo_dumper = PhotoDumper(
        album_path=album_path,
        categories_file=categories_file,
        batch_size=batch_size,
        pre_filter=pre_filter,
        keep_top_k=keep_top_k,
        output_dir=output_dir,
        aesthetic_weight=aesthetic_weight
    )
    click.echo("Grouping photos by category...")
    ranked_categories = photo_dumper.process()
    click.echo("Ranking photos...")
    
    click.echo("\nProcessing complete! Results saved in the 'output' directory.")
    click.echo(f"Selected {sum(len(photos) for photos in ranked_categories.values())} photos across {len(ranked_categories)} categories.")

if __name__ == "__main__":
    main()
